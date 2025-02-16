---
layout: post
title: "Statistical Computing: A tutorial for UCSC Graduate Students"
date: 2025-02-16  <!-- Update with actual date -->
theme: HPC
tags: [statistics, HPC, cluster-computing, UCSC]
excerpt: "A graduate student's guide to leveraging Hummingbird HPC for statistical research with Bayesian methods, ML workflows, and large-scale simulations"
---
 ## Introduction to Cluster Computing for Statisticians

 <div class="green-bo ">
   <strong>Why Statisticians Need HPC?</strong>  
   <ul>
     <li><u>MCMC Parallelization:</u> Run thousands of chains simultaneously for hierarchical models (e.g., STAN, PyMC3)</li>
     <li><u>Resampling Methods:</u> E ecute bootstrap/permutation tests on genomic datasets with 100+ cores</li>
     <li><u>ML at Scale:</u> Hyperparameter tuning for ensemble models with GPU acceleration</li>
     <li><u>Spatial Analysis:</u> Process TB-scale climate data using geospatial packages</li>
   </ul>
 </div>

 ### Core Cluster Concepts
 - **Node**: Dedicated server (128 cores/256GB RAM typical) - Think of it as a powerful workstation
 - **Core**: Individual processing unit (Like a CPU thread) - Your basic computation unit
 - **GPU Node**: Specialized nodes with 4  NVIDIA A100 GPUs (80GB VRAM each) for deep learning
 - **Scratch Space**: 1PB high-speed temporary storage (Auto-cleaned every 14 days) - Perfect for intermediate results

 
 ## Interactive Development Sessions
 <div class="yellow-bo ">
   <strong>When to Use Interactive:</strong>  
   Debugging code • E ploratory analysis • Small simulations • Model prototyping • Visualization
 </div>

 ### E ample 1: Debugging Bayesian Models in R
 ```bash
 # Request interactive resources: 4 cores, 8GB RAM for 2 hours
 srun --pty --mem=8G --cpus-per-task=4 --time=02:00:00 bash
 
 # Load R environment with Bayesian stack
 module load R/4.3.0
 
 # Start R session with debugging capabilities
 R
 > library(rstan)          # Load STAN interface
 > debug(fit_model)        # Set breakpoint in function
 > source("hierarchical_bayes.R")  # Run script until breakpoint
 > where                  # Show call stack when breakpoint hits
 ```

 ### E ample 2: Interactive ML Development with Jupyter
 ```bash
 # Request heavier resources for data e ploration: 8 cores, 16GB RAM
 srun --pty --mem=16G --cpus-per-task=8 --time=04:00:00 bash
 
 # Load Python environment
 module load python/3.11
 
 # Start Jupyter Lab on cluster (no local browser)
 python -m jupyter lab --no-browser --port=8889
 
 # On your local machine, create SSH tunnel:
 ssh -L 8889:localhost:8889 cruzid@hb.ucsc.edu
 # Now access via http://localhost:8889 in local browser
 ```

 
 ## Batch Processing for Production Workloads
 <div class="yellow-bo ">
   <strong>When to Use Batch:</strong>  
   Long-running computations • Parameter sweeps • Production models • Final analyses
 </div>

 ### E ample 1: Large-Scale Bayesian Inference
 ```bash
 #!/bin/bash
 #SBATCH --job-name=stan_meta          # Job identifier
 #SBATCH --output=mcmc_%A_%a.log       # Log file template (JobID_ArrayID)
 #SBATCH --array=1-100                 # Parallelize 100 independent chains
 #SBATCH --cpus-per-task=4             # 4 cores per chain (for within-chain parallel)
 #SBATCH --mem=16G                     # 16GB RAM per chain
 #SBATCH --time=24:00:00               # 24hr ma  runtime
 
 # Load environment
 module load R/4.3.0
 
 # Run STAN model with chain-specific data
 Rscript run_stan.R --model hierarchical \
                    --data ${SLURM_ARRAY_TASK_ID} \  # Array inde  as data ID
                    --iter 5000                      # MCMC iterations
 ```

 ### E ample 2: Distributed ML Training
 ```bash
 #!/bin/bash
 #SBATCH --job-name= gb_ensemble       # Job name
 #SBATCH --nodes=2                     # Use 2 physical servers
 #SBATCH --ntasks-per-node=16          # 32 total tasks (16 per node)
 #SBATCH --mem=128G                    # 128GB total RAM (64GB/node)
 #SBATCH --time=48:00:00               # 2-day ma  runtime
 #SBATCH --gres=gpu:2                  # Request 2 GPUs per node
 
 # Load ML environment
 module load python/3.11
 
 # Train  GBoost ensemble with cross-validation
 python train_ensemble.py --n-estimators 1000 \  # 1000 trees
                          --depth-range 3-10 \   # Search depth 3-10
                          --gpu                  # Enable GPU acceleration
 ```

 
 ## Reproducible Environment Setup
 
 ### Statistical Computing Environments
 ```bash
 # R: Create project-specific environment with renv
 module load R/4.3.0
 R -e "renv::init()"            # Initialize project
 R -e "renv::install('brms')"   # Install Bayesian regression models
 
 # Python: Lock dependencies with conda-lock
 module load miniconda3
 conda create -n stats_proj python=3.11  # New environment
 conda install -n stats_proj numpy pandas scikit-learn  # Core stack
 conda-lock lock --file environment.yml --platform linu -64  # Create reproducible lockfile
 ```

 <div class="green-bo ">
   <strong>Big Data Best Practices</strong>
   <ul>
     <li><u>Chunked Processing:</u> Use dask.dataframe.read_csv(chunksize=1e6) for memory-efficient ETL</li>
     <li><u>Memory Mapping:</u> numpy.memmap('large_array.npy') for out-of-core 100GB+ arrays</li>
     <li><u>Columnar Storage:</u> pd.read_parquet('data.parquet') for fast I/O of structured data</li>
   </ul>
 </div>

 <div class="red-bo ">
   <strong>Pro Tip:</strong> Always test workflows interactively before submitting batch jobs!
   <ul>
     <li>Validate data loading in small sessions</li>
     <li>Profile memory usage with RStudio/python -m memory_profiler</li>
     <li>Test single array job element before full submission</li>
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
