---
layout: post
published: true
title: "A practical Slurm workflow on UCSC Hummingbird"
date: 2025-02-16
updated: 2026-07-29
last_verified: 2026-07-29
theme: Scientific computing
tags: [slurm, hpc, reproducibility, ucsc]
description: "A practical workflow for running statistical computing jobs on UCSC Hummingbird without hard-coding stale cluster details."
excerpt: "Use Hummingbird by discovering current partitions, testing small interactive jobs, controlling threads, and submitting reproducible Slurm batches."
math: false
---

This note is a practical starting point for running statistical computing work on UCSC Hummingbird. It focuses on habits that remain useful when partitions, modules, hardware, and allocation rules change. Do not copy resource requests blindly from an old tutorial. Discover the current system, start small, and scale only after the job has been measured.

Hummingbird is a Slurm-managed cluster. The basic objects are login nodes, compute nodes, partitions, accounts or allocations, jobs, and job steps. The login node is for editing files, submitting jobs, moving modest amounts of data, and checking status. Real computation should run inside an interactive allocation or a batch job.

## Connect and inspect the current system

The open Hummingbird service has used `hb.ucsc.edu`. Some PI-specific allocations may use different entry points, including Elkhorn-managed resources. Follow the instructions for your allocation and verify the endpoint before building automation around it.

After logging in, inspect the live system:

```bash
ssh your_ucsc_id@hb.ucsc.edu
sinfo -o "%P %a %l %D %c %m %G"
scontrol show partition
module avail
```

These commands tell you what partitions exist, whether they are available, their limits, and what modules are currently installed. Treat this output as the source of truth for resource requests.

This discovery step should be repeated when a project is moved to a new allocation or when an old script is reused after a long break. Cluster administrators can change limits, add partitions, retire modules, or redirect specialized resources. A script that was reasonable last year may still run, but it may request resources poorly or rely on software that is no longer the default.

## Keep a reproducible project layout

A stable layout makes batch jobs easier to restart and debug:

```text
project/
  code/
  data/
  config/
  logs/
  results/
  scratch/
```

Keep source code under version control. Store job logs separately from results. Write outputs to a run-specific directory. Avoid editing scripts inside generated result folders because that makes it harder to reconstruct the run later.

## Start with an interactive allocation

Use a small interactive job to test paths, package loading, and one reduced example. The exact partition and limits depend on the current system, so adjust after checking `sinfo` and your allocation policy.

```bash
srun --pty --cpus-per-task=1 --mem=4G --time=00:30:00 bash
hostname
pwd
```

Inside that shell, run the smallest version of the analysis. For R:

```bash
module avail R
module load R
R --vanilla
```

For Python:

```bash
module avail python
module load python
python --version
```

If your work uses user-level environments, create them in your home or project space rather than relying on one fixed module version. Record how the environment was created.

## Use conservative batch scripts

A batch script should request only what the job can use. Over-requesting memory, CPUs, or wall time makes scheduling harder and can hide inefficient code.

```bash
#!/usr/bin/env bash
#SBATCH --job-name=fit_model
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs results

module load R

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

Rscript --vanilla code/run_model.R --config config/base.yml --out results/run_${SLURM_JOB_ID}.rds
```

The thread variables matter. Many R and Python numerical libraries use threaded BLAS or OpenMP. If a Slurm array starts many tasks and each task also starts many threads, the job can oversubscribe the allocated CPUs. Decide whether parallelism happens across processes or inside one process, then request resources accordingly.

## Job arrays

Arrays are useful for independent chains, simulation replicates, bootstrap runs, or scenario sweeps.

```bash
#!/usr/bin/env bash
#SBATCH --job-name=sim_array
#SBATCH --array=1-100
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs results

if [[ -z "${SLURM_ARRAY_TASK_ID:-}" ]]; then
  echo "Missing SLURM_ARRAY_TASK_ID" >&2
  exit 1
fi

module load R
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript --vanilla code/run_simulation.R \
  --replicate "${SLURM_ARRAY_TASK_ID}" \
  --out "results/sim_${SLURM_ARRAY_TASK_ID}.rds"
```

Validate the array index inside the analysis script as well. A missing or out-of-range index should fail fast rather than overwrite a default output.

## Monitor and size jobs empirically

Submit, inspect, and adjust:

```bash
sbatch code/job.sh
squeue -u "$USER"
sacct -j JOBID --format=JobID,State,Elapsed,MaxRSS,ReqMem,ExitCode
tail -n 80 logs/fit_model_JOBID.out
tail -n 80 logs/fit_model_JOBID.err
```

Use `sacct` output to tune future requests. If a job used 1.5 GB, requesting 64 GB is not justified. If it died from memory pressure, increase memory or change the algorithm. If it hit the time limit, checkpoint intermediate results and estimate runtime from smaller runs.

## Jupyter through an allocation

Run Jupyter on a compute node, not on the login node. First request an allocation. Then start Jupyter without opening a browser:

```bash
srun --pty --cpus-per-task=2 --mem=8G --time=02:00:00 bash
hostname
jupyter lab --no-browser --ip=127.0.0.1 --port=8888
```

From your local machine, open an SSH tunnel through the login host to the allocated compute node. Replace `COMPUTE_NODE` with the hostname printed inside the allocation:

```bash
ssh -L 8888:COMPUTE_NODE:8888 your_ucsc_id@hb.ucsc.edu
```

Then open the local URL shown by Jupyter. Shut down the server and release the allocation when finished.

## Checkpoints and dependencies

Long jobs should be restartable. Save intermediate outputs, write final results atomically when possible, and avoid a single monolithic job that loses all progress if it fails near the end. Slurm dependencies can chain stages:

```bash
first=$(sbatch --parsable code/preprocess.sh)
sbatch --dependency=afterok:${first} code/fit_model.sh
```

Do not hard-code private paths, module versions, GPU syntax, or partition names in public instructions. Put allocation-specific details in a local README or configuration file that can be updated independently.

For statistical work, the most common failure is not that Slurm is complicated. It is that the analysis script assumes an interactive laptop environment. Batch jobs should not depend on the current working directory being guessed correctly, on a package being installed only in an interactive shell, or on a plot window opening. Write scripts so that all inputs, outputs, and configuration files are explicit. Then test the exact command inside a small allocation before scaling to an array or a long run.

## References

- UCSC Hummingbird. [Getting started documentation](https://hummingbird.ucsc.edu/getting-started/).
- SchedMD. [Slurm job array documentation](https://slurm.schedmd.com/job_array.html).
