
# 🌟 R GSoC 2025 Application

## Project Information

- **Project Title:** Fast and Flexible Dynamic Quantile Inference: exDQLM
- **Short Title (≤30 chars):** exDQLM: Dynamic Quantile Modeling
- **Project Idea Page:** [Insert URL] (to be updated)

---

## 👤 Contributor Bio

### **About Me**
I am a **4th-year Ph.D. candidate** in **Statistics** at the [University of California, Santa Cruz (UCSC)](https://engineering.ucsc.edu/departments/statistics/). My research focuses on **Bayesian Statistics**, **Spatio-Temporal Modeling**, and **Machine Learning**, with a strong emphasis on developing **scalable** and **interpretable** forecasting methodologies.

I am advised by [Dr. Bruno Sansó](https://users.soe.ucsc.edu/~bruno/) and [Dr. Raquel Prado](https://raquel.soe.ucsc.edu/). My research applies **Dynamic Quantile Regression**, **Sequential Monte Carlo (SMC) methods**, and **forecast synthesis techniques** to **applied challenges** in **climate forecasting** and **hydrology**.

I hold a **B.Sc. in Applied Mathematics** (with an emphasis on **Numerical Analysis**) and an **M.Sc. in Economics** (specializing in **Econometrics**) from [Instituto Tecnológico Autónomo de México (ITAM)](https://www.itam.mx/).

## Technical Expertise

I have **10+ years of experience** working with **R** and **MATLAB** for **statistical modeling, computational inference, time series analysis, and numerical computing**. Additionally, I have **8+ years of experience** in **Python** and **C++**, which I use extensively for **high-performance computing, Bayesian inference, and statistical simulations**.

###  **Software & Programming Skills**
- **Languages:** R, MATLAB, Python, C++, SQL, Bash
- **Tools & Frameworks:** Git, Bitbucket, DBeaver, Rcpp, OpenMP
- **OS & Systems:** Linux (Ubuntu), macOS, Windows
- **Data & HPC:** Parallel Computing, Cloud Storage, Spatio-Temporal Modeling, Forecasting

---

### I. **Academic & Research Experience**
#### **Ph.D. Research at University of California, Santa Cruz (UCSC)**
- Developing **Bayesian Dynamic Quantile Models (DQLMs)** for probabilistic forecasting in climate and environmental sciences.
- Extensive use of **Sequential Monte Carlo (SMC), Variational Bayes, and Posterior Predictive Synthesis** for scalable Bayesian inference.

#### **Software work at Publications**
- **[Aguirre, A., Lobato, I.N. (2024)](https://doi.org/10.1007/s00181-024-02564-5)**  
  *Evidence of Non-Fundamentalness in OECD Capital Stocks.*  
  - Developed and implemented all **computational algorithms** in **MATLAB** and **C++**.

- **[Lobato, I. N., Velasco, C. (2022)](https://doi.org/10.1093/ectj/utac001)**  
  *Single Step Estimation of ARMA Roots for Non-Fundamental Nonstationary Fractional Models.*  
  - Led all **algorithmic development, implementation, and journal-requested revisions** using **Python**, **MATLAB**, and **C++**.

---

### II. **Professional Experience**
#### **Computer Systems Coordinator at UCSC Statistics Department (2023 – Present)**
- **Linux Systems Administration:** Maintain and optimize department **servers** for faculty and research use.
- **Technical Support & Compliance:** Collaborate with UCSC IT to align department resources with university policies.
- **User Support & Resource Allocation:** Assist faculty and graduate students with **server usage, software installation, and issue resolution**.

#### **Data Analyst at NeatLeaf Inc. (2021 – 2022, Scotts Valley, CA)**
- **Data Engineering & Automation:** Built an automated **data pipeline** for real-time microclimate monitoring in greenhouses.
- **Spatio-Temporal Modeling:** Developed a **statistical model** for detecting **air anomalies** in greenhouse environments.
- **Sensor Calibration & Diagnostics:** Calibrated **temperature, humidity, and CO2 sensors (BME680 & SCD41)**.
- **Performance Reporting & Compliance:** Provided **weekly reports** adhering to **Google Coding Standards**.

### **Why I’m a Strong Fit**
- **Expertise in R & Bayesian Modeling:** Extensive experience in R, particularly for **Bayesian time series analysis, probabilistic forecasting, and statistical learning**.
- **Proven Research & Development Experience:** Strong background in **quantile-based inference, state-space models, and scalable computational Bayesian methods**.
- **Software Development & Open-Source Contribution:**  
  - Developed and optimized **high-performance statistical algorithms** in **R, Python, MATLAB, and C++**.
  - Committed to **reproducible research, open-source development, and efficient software design**.
    
- **Curriculum Vitae:** [View my CV](https://www.antonio-aguirre.com/cv/)
  
---

## Contact Information

- **Full Name:** Antonio Aguirre  
- **Email:** jaguir26 (at) ucsc.edu, antonio.agprz (at) gmail.com  
- **Phone Number:** 831-515-9264  
- **Affiliation:** University of California, Santa Cruz (UCSC)  
- **Program & Stage of Completion:** 4th-year Ph.D. Candidate in Statistics
- **Preferred Communication Channels:** Email, Phone, WhatsApp (same as Phone Number)  

---

## Schedule Conflicts

- **Potential Conflicts:** Teaching Assistant (TA) or Instructor responsibilities during the summer.
- **Mitigation Plan:** 
  - My past experience managing both research and teaching responsibilities ensures that this won’t affect my work on GSoC.
  - If I am an instructor, I will have **TAs assisting with grading**.
  - **Summer sessions allow remote teaching**, eliminating the need for daily commuting and allowing me to dedicate full-time effort to GSoC.

---

##  Mentors

- **Evaluating Mentor:**  
  - **Rebecca Killick** (Lancaster University, UK) – r.killick@lancaster.ac.uk  
- **Co-Mentor:**  
  - **Raquel Barata** (Penn State University, USA) – rxb875@psu.edu  
- **Communication with Mentors:**  
  - I have been actively communicating with **Rebecca Killick**, discussing project goals, software integration, and implementation strategies.
  - **Raquel Barata** has expressed strong interest in staying involved, as my research aligns closely with her work. We maintain frequent communication and plan to collaborate on this and future projects.

---

## Coding Plan & Methods

### **Development Overview**
- **Core Enhancements:**  
  - Refactor the current implementation of **Bayesian Dynamic Quantile Regression Models (exDQLM)** for **time-series quantile estimation**.  
  - Implement **Variational Bayes (VB) & Markov Chain Monte Carlo (MCMC) inference** in **C++** for improved efficiency.  
  - Introduce a **Laplace/Delta approximation** to handle **non-conjugate parameters** in VB updates.  
  - Extend functionality to **static quantile regression** using the **Extended Asymmetric Laplace (exAL) distribution**.  
  - Develop a **parallel inference framework** to estimate multiple quantiles efficiently.  
  - Implement **Posterior Predictive Quantile Synthesis (PPQS)** ensuring **non-crossing quantile estimates**.  
  - Support additional features:  
    - **Missing Data Handling**   
    - **Multivariate Time Series Support** for joint quantile forecasting.  

---

### **Approach to Development**
- **Modular Implementation:**  
  - Develop separate **core functions** for **posterior inference, quantile prediction, and uncertainty quantification**.  
  - Implement **efficient variational approximations** for handling large datasets with **real-time inference capabilities**.  

- **Computational Efficiency & Parallelization:**  
  - **Optimize code using C++ (`Rcpp` & `RcppParallel`)** for faster inference and large-scale applications.  
  - Implement **multi-threaded execution** to support computational scalability.  

- **Software Design & API Integration:**  
  - Ensure **seamless compatibility** with key R packages such as `rstan` and `bayesplot`.  
  - Follow **tidyverse design principles** for an intuitive API and maintainability.  
  - Implement **comprehensive function documentation** with `roxygen2`.  

---

### **Integration with Existing Workflows**
- **Modeling & Forecasting:**  
  - Enable easy integration with **dynamic Bayesian models** for **time-series forecasting**.  
  - Provide a **flexible framework** to extend Bayesian quantile estimation for various applications.  

- **Performance Optimization:**  
  - Utilize **C++-based inference methods** for **scalable and efficient computation**.  
  - Support **large-scale inference** using parallel computing frameworks.  

- **Usability & Visualization:**  
  - Ensure **compatibility with `ggplot2`** for **intuitive visualization** of quantile estimates.
  - Ensure **compatibility with `bayesplot`** `for a standard bayesian model evaluation.
  - Leverage `tidyverse` for seamless **data handling and processing**.  
  - Maintain **CRAN compliance** for package accessibility and long-term usability.  

---

### **Testing & Validation**
- **Unit tests & debugging strategy:**  
  - Implement **unit tests** for each module using `testthat` and `RcppUnit`.  
  - Validate posterior distributions using **synthetic datasets** with known quantile properties.  
  - Conduct **Monte Carlo simulations** to test model stability under various scenarios.  

- **Benchmarks & performance validation:**  
  - Compare `exDQLM` against existing R packages (`quantreg`, `bayesQR`, `qrjoint`, `dynquant`).  
  - Measure runtime performance across **small, medium, and large datasets**.  
  - Evaluate **memory efficiency** using large-scale datasets in hydrology and finance.  

| Feature                    | quantreg | dynquant | SPQR | qrjoint | bayesQR | lqr  | exDQLM |
|----------------------------|----------|---------|------|---------|---------|------|--------|
| **Frequentist Approach**   | ✅       | ✅      | ❌   | ✅      | ❌      | ✅   | ✅     |
| **Bayesian Inference**     | ❌       | ❌      | ✅   | ✅      | ✅      | ❌   | ✅     |
| **Time-Dependent Data**    | ❌       | ✅      | ❌   | ❌      | ❌      | ❌   | ✅     |
| **Covariates**             | ✅       | ❌      | ✅   | ❌      | ✅      | ✅   | ✅     |
| **Scalability (Large Data)** | ❌       | ✅      | ✅   | ❌      | ✅      | ✅   | ✅     |
| **Non-Linear Regression**  | ✅       | ❌      | ✅   | ❌      | ❌      | ❌   | ❌     |
| **Multivariate Response**  | ✅       | ❌      | ❌   | ❌      | ❌      | ❌   | ✅     |
| **Missing Data Handling**  | ❌       | ❌      | ❌   | ❌      | ❌      | ✅   | ✅     |
| **Non-Crossing Quantiles** | ❌       | ❌      | ✅   | ✅      | ❌      | ❌   | ✅     |

---

### **Challenges & Risk Mitigation**
- **Potential Obstacles:**  
  - **Computational Limits:** Large-scale Bayesian quantile inference can be computationally expensive.  
  - **Algorithmic Complexity:** Ensuring **non-crossing quantiles** and proper posterior synthesis.  
  - **Scalability Issues:** Efficiently handling high-dimensional covariates and multivariate responses.  

- **Proposed Solutions:**  
  - Optimize via **Variational Bayes (VB)** for faster inference over traditional MCMC.  
  - Implement **Rcpp-based parallel processing** to reduce computational overhead.  
  - Use **Robust Cholesky and SVD factorization and variational inference techniques** to stabilize large-matrix computations.  
  - Conduct **extensive testing** on benchmark datasets to fine-tune efficiency.  
  - Leverage **Posterior Predictive Synthesis (PPQS)** to ensure a unified and interpretable estimation of various quantiles.  


---

- CHECK IT AGAIN AND MAKE SENSE. 
- WHEN TO DO THE STATIC? 
- WHEN AND HOW TO DO EVALUATION? CONSIDER bayesplot Package?
- LIST ALL FEATURES OF THE MODEL AND ORGANIZE THEM HOWEVER MAKES MORE SENSE AND FOR WHICH I ALREADY HAVE CODE. 

## 📆 Timeline

### **Week 1-4: Pre-Coding Period (Community Bonding) (May 8 – June 1, 2025)**
**Goal:** Establish a solid foundation for the project by setting up the development environment, refining the project scope, and engaging with the R community.

#### **Tasks**
- Set up the **GitHub repository**, version control, and CI/CD workflows.
- Study and analyze existing R packages for qusntile regression (`quantreg`, `bayesQR`, `qrjoint`).
- Familiarize with **state-space modeling**, **Bayesian quantile regression**, and **Variational Bayes**.
- Finalize the **technical roadmap** with mentors.
- Define the **API structure** and overall package design, and ensure compatibility with `bayesplot`.
- Engage with the **R open-source community** for early feedback.

#### **Deliverables**
- Established **repository** with project documentation.
- Initial API **blueprint** and function specifications.
- Community engagement and feedback collection.

---

### **Week 5-6: Coding Phase 1 (June 2 – June 17, 2025)**
**Goal:** Implement core functionalities of exDQLM.

#### **Tasks**
- Develop the **Bayesian Dynamic Quantile Regression (DQLM)** theoretical framework.
- Implement **Kalman filtering and state-space model estimation** in `Rcpp` for speed.
- Create **posterior update functions** for time-dependent quantile inference.
  - Implement **MCMC-based inference** for dynamic quantiles.
  - Implement **Variational Bayes (VB)** inference approximation for conjugate parameters (using **Laplace/Delta techniques**).
- Develop **unit tests** using `testthat` for core functions.
- Validate implementation with **synthetic datasets**.
- Draft function documentation (input/output specifications).

#### **Deliverables**
- Functioning **exDQLM** model.
- Early **unit tests** ensuring stable implementation.
- Initial **benchmark tests** against `quantreg` and `bayesQR`.

---

### **Week 7-8: Coding Phase 2 (June 18 – July 15, 2025)**
**Goal:** Expand core functionality, optimize inference, and refine package structure.

#### **Tasks**
- Implement **Posterior Predictive Quantile Synthesis (PPQS)** for non-crossing quantile estimation.
- Develop **parallel execution support** via `RcppParallel` for large-scale inference.
- Conduct **initial performance benchmarks** on real-world datasets (financial time series, hydrology).
- Develop the **Bayesian Static Quantile Regression (DQLM)** theoretical framework under the Extended Asymmetric Laplace 
- Expand **documentation** to include usage examplesDistribution (exAL). 

#### **Deliverables**
- Fully functional **exDQLM** dynamic quantile regression model.
- Fully functional **exDQLM** static quantile regression model.
- Optimized **VB & MCMC inference** methods.
- Initial **performance benchmarks** and **real-world dataset tests**.

---

### **Week 9: Mid-Term Evaluation (July 14 – 18, 2025)**
**Goal:** Conduct evaluation of progress and ensure the project is on track.

#### **Tasks**
- Review progress with mentors and address feedback.
- Ensure **functionality alignment with project goals**.
- Debug and refine **posterior synthesis & inference methods**.
- Conduct **extended validation tests** on unseen datasets.
- Finalize the **first draft of documentation**.

#### **Deliverables**
- Mid-term **progress report**.
- Fully tested **core model implementation**.
- Review meeting with mentors.

---

### **Week 10-11: Final Coding Phase (July 16 – August 2, 2025)**
**Goal:** Complete implementation, optimize performance, and enhance usability.

#### **Tasks**
- Finalize **MCMC and Variational Bayes optimizations**.
- Improve computational performance using **vectorized operations** in `Rcpp`.
- Conduct **stress testing** on large datasets.
- Implement **visualization tools** for dynamic quantile estimation.
- Develop **comprehensive vignettes** and **tutorials**.
- Refactor code for **robustness and maintainability**.

#### **Deliverables**
- Fully optimized `exDQLM` package.
- Efficient **scalable inference** methods.
- Finalized **visualization components**.
- Comprehensive **testing and validation results**.

---

### **Week 12-13: Final Submission & Review (August 3 – August 19, 2025)**
**Goal:** Polish the project and prepare for CRAN submission.

#### **Tasks**
- Finalize **documentation, README, and package manual**.
- Ensure **compliance with CRAN submission standards**.
- Conduct **final peer review** with mentors.
- Prepare a **detailed project report** summarizing key developments.
- Submit `exDQLM` to **CRAN and GitHub**.

#### **Deliverables**
- **CRAN-ready** `exDQLM` package.
- Completed **documentation and tutorials**.
- Final project **submission report**.

---

### **Week 14+: Post-GSoC Maintenance & Future Work**
**Goal:** Ensure continued development and usability of the package.

#### **Tasks**
- Address **community feedback** post-release.
- Monitor **GitHub issues and bug reports**.
- Plan potential **enhancements and future contributions**.
- Engage in **conference presentations** or write a research paper based on exDQLM.

#### **Deliverables**
- Publicly available `exDQLM` package with continued support.
- Defined roadmap for **future updates**.


---

### **Contingency Plan**
- **Delays in Implementation:** If certain functions take longer than expected, I will prioritize core functionalities before advanced features.
- **Computational Challenges:** If scaling issues arise, I will work with mentors to refine **memory management and parallel execution strategies**.
- **Unexpected Bugs:** I will ensure **continuous debugging and testing** throughout the project to minimize end-phase setbacks.
- **Time Conflicts:** I will front-load work in early phases and adjust my summer schedule accordingly.

---

## **Why This Timeline is Strong**
✔ **Clear milestones** and deliverables at every stage.  
✔ **Balanced development**—core functionality first, optimization later.  
✔ **Real-world testing** and **benchmarking against existing packages**.  
✔ **Contingency planning** to handle setbacks.  

Would you like any refinements before integrating it into the full document? 🚀

---
## Contingency Plan

### **What if something goes wrong?**
Despite careful planning, unexpected challenges may arise. Below are strategies to mitigate potential risks:

- **Delays in Implementation:**  
  - Prioritize **core functionalities** (e.g., Bayesian Dynamic Quantile Regression, Posterior Predictive Synthesis) over advanced features.  
  - If necessary, shift some enhancements (e.g., visualization tools, extra model comparisons) to post-GSoC development.  

- **Computational Challenges:**  
  - Optimize performance using **Rcpp and parallel execution** from the start.  
  - Implement **efficient memory management** to handle large-scale data.  
  - Benchmark against existing tools early to identify bottlenecks.  

- **Unexpected Bugs or Algorithmic Issues:**  
  - Regular unit tests and **debugging routines** (automated CI/CD workflows).  
  - Frequent mentor check-ins to address issues **before they escalate**.  
  - Maintain a **debugging and troubleshooting log** for tracking errors and solutions.  

- **Time Conflicts or Personal Constraints:**  
  - **Front-load coding tasks** to create a buffer for unexpected delays.  
  - Adjust workload around **teaching responsibilities** (remote teaching makes this feasible).  
  - Maintain weekly updates with mentors to **keep the project on track**.  

- **Mentor Unavailability or External Factors:**  
  - Maintain **open communication** with multiple mentors to ensure continuity.  
  - Engage with the **R community** for external feedback and code review.  

---

## Management of Coding Project

### **Version Control Strategy**
- The project will be **hosted on GitHub** with a structured repository:
  - `main` branch for stable releases.  
  - `dev` branch for active development.  
  - Feature-specific branches (`feature/parallelization`, `feature/variational_bayes`, etc.).  
  - **Issue tracking & pull requests** for organized progress monitoring.  
  - **CI/CD pipeline** for automated testing.  

### **Commit Frequency**
- **Daily commits** during active development.  
- **Milestone-based commits** (weekly) for structured review.  
- **Peer-reviewed pull requests** before merging major changes.  
- **Comprehensive commit messages** to ensure reproducibility.  

### **Performance Tracking**
- **Unit testing** via `testthat` to ensure correctness.  
- **Benchmarking scripts** to compare speed and efficiency against existing packages (`quantreg`, `bayesQR`).  
- **Validation through real-world data** (hydrology, finance).  
- Continuous integration setup for **automated testing and code quality checks**.  

---

## ✅ Qualification Task

### **Test Submitted to Mentors**
- To validate my ability to execute this project, I developed a **prototype implementation** of a Bayesian Dynamic Quantile Model in R. This included:
  - **Implementation of the Extended Asymmetric Laplace (exAL) distribution.**  
  - **Basic state-space quantile modeling using Kalman Filtering.**  
  - **Variational inference for scalable quantile regression.**  
  - Performance benchmarking against `quantreg` and `bayesQR`.  

#### **Example Code Snippet**
```r

```

- **Example of Previous Related Work:** [Link to GitHub repositories, papers, or projects]  

---

##  Final Thoughts

This application presents a structured and well-planned roadmap to successfully implement **exDQLM** within the GSoC 2025 timeframe. By integrating **Bayesian Dynamic Quantile Regression**, **scalable inference methods**, and **robust model validation**, this project will significantly enhance the R ecosystem for quantile-based modeling.

With well-defined objectives, contingency strategies, and an **efficient development workflow**, I am confident that this project will provide **a valuable open-source tool** for researchers, analysts, and practitioners working with time-dependent quantile estimation. 

I look forward to **feedback, mentorship, and collaboration** to refine and enhance this project for maximum impact.


**Best,**  
**Antonio Aguirre**  

---

### Contact Information  

📧 **Email:** jaguir26@ucsc.edu | antonio.agprz@gmail.com  
🔗 **GitHub:** [AntonioAPDL](https://github.com/AntonioAPDL)  
🌐 **Website:** [antonio-aguirre.com](https://antonio-aguirre.com)  

