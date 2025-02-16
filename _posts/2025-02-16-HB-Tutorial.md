---
layout: post
title: "Statistical Computing: A tutorial for UCSC Graduate Students"
date: 2025-02-16  <!-- Update with actual date -->
theme: HPC
tags: [statistics, HPC, cluster-computing, UCSC]
excerpt: "A graduate student's guide to leveraging Hummingbird HPC for statistical research with Bayesian methods, ML workflows, and large-scale simulations"
---
 ## Introduction to Cluster Computing for Statisticians

 <div class="green-box ">
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
 <div class="yellow-box ">
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
 <div class="yellow-box ">
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

 <div class="green-box ">
   <strong>Big Data Best Practices</strong>
   <ul>
     <li><u>Chunked Processing:</u> Use dask.dataframe.read_csv(chunksize=1e6) for memory-efficient ETL</li>
     <li><u>Memory Mapping:</u> numpy.memmap('large_array.npy') for out-of-core 100GB+ arrays</li>
     <li><u>Columnar Storage:</u> pd.read_parquet('data.parquet') for fast I/O of structured data</li>
   </ul>
 </div>

 <div class="red-box ">
   <strong>Pro Tip:</strong> Always test workflows interactively before submitting batch jobs!
   <ul>
     <li>Validate data loading in small sessions</li>
     <li>Profile memory usage with RStudio/python -m memory_profiler</li>
     <li>Test single array job element before full submission</li>
   </ul>
 </div>

 ## Performance Optimization Guide

 <div class="yellow-box">
   <strong>Understanding Cluster Resources</strong>
   <ul>
     <li>All compute happens on <u>remote servers</u> - your laptop just submits jobs</li>
     <li>Storage paths like /hb/home are <u>network-mounted</u> - accessible from all nodes</li>
     <li>Always test scripts with small resources first!</li>
   </ul>
 </div>

 ### Memory Management Essentials
 ```bash
 # For R: Profile memory usage with Valgrind
 # This creates detailed memory usage reports
 module load R/4.3.0
 R -d "valgrind --tool=massif" -f bayesian_analysis.R
 # After running, analyze with:
 ms_print massif.out.* > memory_report.txt
 
 # For Python: Track memory allocation
 # First install memory profiler in your environment
 pip install memray
 # Run profiling and generate report
 python -m memray run -o profile.bin ml_pipeline.py
 python -m memray stats --json profile.bin > memory_stats.json
 ```

 <div class="green-box">
   <strong>Why Memory Matters:</strong>
   <ul>
     <li>Jobs exceeding requested memory get <u>automatically killed</u></li>
     <li>Use 10-20% less than node maximums for safety</li>
     <li>Monitor memory during runs with <code>seff JOBID</code></li>
   </ul>
 </div>

 ### Parallel Computing Patterns Explained
 <table>
   <tr>
     <th>Method</th>
     <th>SLURM Directives</th>
     <th>When to Use</th>
     <th>Example Command</th>
   </tr>
   <tr>
     <td>Embarrassing Parallel</td>
     <td>--array=1-100</td>
     <td>Independent tasks (Bootstrap/permutation tests)</td>
     <td><code>sbatch --array=1-100 job.sh</code></td>
   </tr>
   <tr>
     <td>MPI (Message Passing)</td>
     <td>--nodes=4 --ntasks-per-node=16</td>
     <td>Inter-process communication (Gibbs sampling)</td>
     <td><code>mpirun -np 64 ./model</code></td>
   </tr>
   <tr>
     <td>Multithreading</td>
     <td>--cpus-per-task=32</td>
     <td>Shared-memory tasks (XGBoost/CV tuning)</td>
     <td><code>export OMP_NUM_THREADS=32</code></td>
   </tr>
 </table>

 <div class="green-box">
   <strong>Key Concept:</strong> Always match parallel method to your algorithm:
   <ul>
     <li>Embarrassing Parallel: No data sharing between tasks</li>
     <li>MPI: Needs data exchange between processes</li>
     <li>Multithreading: Single process with multiple threads</li>
   </ul>
 </div>

 
 ## Getting Help with HPC
 
 <div class="green-box">
   <strong>Cluster Support Channels</strong>
   <ul>
     <li><a href="mailto:hummmingbird@ucsc.edu">Email Support</a>: For technical issues</li>
     <li><a href="https://join.slack.com/t/ucschummingbi-lph3072/shared_invite/zt-19mbwqvx1-GqguQcumVBLss~nzjOHAYg">Slack Channel</a>: Real-time help from users</li>
     <li>Documentation: https://hummingbird.ucsc.edu/docs</li>
   </ul>
 </div>

 ```bash
 # Check job efficiency - run this while job is active
 seff $(squeue -u $USER -h -o %i)
 # Look for:
 # - CPU Utilization: Should be >90% for good efficiency
 # - Memory Usage: Should be < requested amount
 ```

 <div class="red-box">
   <strong>Avoid These Common Mistakes</strong>
   <ul>
     <li><u>Memory Overallocation:</u><br>
     Bad: <code>--mem=256G</code> (max is 256GB/node)<br>
     Good: <code>--mem=230G</code> (leave 10% margin)</li>
     
     <li><u>Ignoring Error Logs:</u><br>
     Always check <code>slurm-JOBID.err</code> after failures</li>
     
     <li><u>Local Installs:</u><br>
     Never use <code>pip install --user</code> - it can break cluster environments</li>
   </ul>
 </div>

