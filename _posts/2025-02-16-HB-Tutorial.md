---
layout: post
title: "Statistical Computing on UCSC Hummingbird HPC"
date: 2025-02-16  <!-- Update with actual date -->
theme: HPC
tags: [statistics, HPC, cluster-computing, UCSC]
excerpt: "A graduate student's guide to leveraging Hummingbird HPC for statistical research with Bayesian methods, ML workflows, and large-scale simulations"
---

## Introduction to Cluster Computing for Statisticians

<div class="green-box">
  <strong>Why Statisticians Need HPC?</strong>  
  <ul>
    <li>Parallelize 10,000 MCMC chains for hierarchical models</li>
    <li>Run bootstrap resampling on 100-core genomic datasets</li>
    <li>Train ensemble ML models with hyperparameter grid searches</li>
    <li>Process spatial statistics on TB-scale climate data</li>
  </ul>
</div>

### Key Concepts Explained
- **Node**: Physical server (128-core/256GB RAM typical)
- **Core**: CPU thread for task parallelism  
- **GPU Node**: 4x A100 GPUs for deep learning  
- **Scratch Space**: 1PB temporary storage (auto-cleaned every 14 days)


## Interactive Workflows for Statistical Development

<div class="yellow-box">
  <strong>Debugging Bayesian Models</strong>  
  ```bash
  srun --pty --mem=8G --cpus-per-task=4 --time=02:00:00 bash
  module load R/4.3.0
  R
  > library(rstan)
  > debug(fit_model)  # Set breakpoint
  > source("hierarchical_bayes.R")  # Trigger debug mode
  ```
</div>

<div class="green-box">
  <strong>Live EDA with Dask</strong>  
  ```bash
  srun --pty --mem=16G --cpus-per-task=8 --time=04:00:00 bash
  module load python/3.11
  python -m jupyter lab --no-browser --port=8889
  # SSH tunnel to local machine: ssh -L 8889:localhost:8889 cruzid@hb.ucsc.edu
  ```
</div>


## Batch Processing: Statistical Workload Templates

### Bayesian MCMC at Scale  
```bash
#!/bin/bash
#SBATCH --job-name=stan_meta
#SBATCH --output=mcmc_%A_%a.log  # %A=job ID, %a=array index
#SBATCH --array=1-100  # 100 parallel chains
#SBATCH --cpus-per-task=4  # 4 threads per chain
#SBATCH --mem=16G
#SBATCH --time=24:00:00

module load R/4.3.0
Rscript run_stan.R --model hierarchical --data ${SLURM_ARRAY_TASK_ID} --iter 5000
```


### Machine Learning Pipeline  
```bash
#!/bin/bash
#SBATCH --job-name=xgb_ensemble
#SBATCH --nodes=2  # 2 servers
#SBATCH --ntasks-per-node=16  # 32 total tasks
#SBATCH --mem=128G 
#SBATCH --time=48:00:00

module load python/3.11
python train_ensemble.py --n-estimators 1000 --depth-range 3-10 --gpu
```


## Advanced Statistical Computing Features

<div class="green-box">
  <strong>Reproducible Environments</strong>  
  ```bash
  X# R environment with renv
  Xmodule load R/4.3.0
  XR -e "renv::init(); renv::install('brms')"
  
  # Python with conda-lock
  module load miniconda3
  conda create -n stats_proj python=3.11
  conda-lock lock --file environment.yml --platform linux-64
  ```
</div>

<div class="yellow-box">
  <strong>Big Data Strategies</strong>
  <ul>
    <li>Chunked Processing: Use dask.dataframe for >1GB CSVs</li>
   <li>Memory Mapping: numpy.memmap for 100GB+ arrays</li>
    <li>Columnar Storage: Parquet/Feather over CSV</li>
  </ul>
</div>


## Performance Optimization Guide

### Memory Management
```bash
# Monitor R memory
module load R/4.3.0
R -d "valgrind --tool=massif" -f bayesian_analysis.R

# Python memory profiling
pip install memray
python -m memray run -o profile.bin ml_pipeline.py
```


### Parallel Computing Patterns
<table>
  <tr>
    <th>Method</th>
    <th>SLURM Directives</th>
    <th>Use Case</th>
  </tr>
  <tr>
    <td>Embarrassing Parallel</td>
    <td>--array=1-100</td>
    <td>Bootstrap/permutation tests</td>
  </tr>
  <tr>
    <td>MPI</td>
    <td>--nodes=4 --ntasks-per-node=16</td>
    <td>Gibbs sampling</td>
  </tr>
  <tr>
    <td>Multithreading</td>
    <td>--cpus-per-task=32</td>
    <td>XGBoost/CV tuning</td>
  </tr>
</table>


## Department-Specific Resources

<div class="green-box">
  <strong>Statistics HPC Support</strong>
  <ul>
    <li>Pre-built Environments: /hb/software/stats</li>
    <li>Datasets: /hb/groups/statdata</li>
    <li>Consultations: Tues/Thurs 2-4pm AP&M 2312</li>
    <li>Email: stats-hpc@ucsc.edu</li>
  </ul>
</div>

```bash
# Quick job health check
seff $(squeue -u $USER -h -o %i)
```


<div class="red-box">
  <strong>Common Pitfalls</strong>
  <ul>
    <li>Oversubscribing memory: Use --mem-per-cpu for array jobs</li>
    <li>Ignoring exit codes: Always check *.err logs</li>
    <li>Local package installs: Use conda/renv instead</li>
  </ul>
</div>
