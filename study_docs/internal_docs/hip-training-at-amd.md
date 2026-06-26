# HIP Training at AMD

> **Source URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531791935/HIP+Training+at+AMD
> **pageId:** `531791935`
> **Space:** LC (Learning Center)
> **Version:** 21 (last updated 2025-05-06)
> **Fetched on:** 2026-06-26 (via Atlassian Confluence MCP, `contentFormat=markdown`)
>
> This file contains the full markdown of the "HIP Training at AMD" hub page **plus**
> the full content of every meaningful descendant page (the 100/200/300-level course
> pages). Each sub-page section is labeled with its own title, Confluence URL, and pageId.
>
> **Note on embedded media:** The course pages embed videos and slide decks as Confluence
> media (`blob:` attachments) which are **not** retrievable as text via the MCP — only the
> course outlines, homework descriptions, and inline code survive in markdown. The actual
> slide decks are therefore not reproduced here. (See `Accelerated_Computing_with_HIP_Internal.pdf`
> in the repo root, a ~16 MB slide deck that likely contains presentation content not present
> on these Confluence pages.) Many course videos are also mirrored at the external Notion
> site: https://syifan.notion.site/AMD-HIP-Training-Course-86cb772392dc45d9bc19f7018878505c

---

# Intro

Welcome to the hub page for all **HIP** training resources. This page is your guide for accessing all course material and training resources for using **HIP** in _**AMD's Software Org**_.

_(Image: HIP training banner — embedded Confluence media, not fetchable.)_

# Points of Contact

| **Person** | **Course Role** |
| --- | --- |
| @Former user (Deleted) | Subject Matter Expert |
| @Former user (Deleted) | Subject Matter Expert |
| @Mishra, Pulakit | SSE Training Admin |
| @Creighton, Brendan | SSE Training Admin |

# Course Breakdown

_(Image: course breakdown graphic — embedded Confluence media, not fetchable.)_

## HIP 100 Level (Beginner)

**Who are these courses for?**

* Everyone at AMD
* Developers new to HIP

**Things covered in these courses**

* What is HIP and why is it important to AMD - Introduction
* Fundamentals of HIP Programming
* HIP Programming Examples and Tutorials

    * HIP Kernel Language
    * Debugging
    * HIP Hierarchy
    * Vector Add
    * Matrix Transpose
    * Concurrency and Overlapping Operations in HIP
    * Thread Synchronization

* AMD GPU Architecture

## HIP 200 Level (Intermediate)

**Who are these courses for?**

* Developers new to HIP

**Things covered in these courses**

* HIP Tools

    * ROCm Info
    * ROCm SMI
    * ROCm Profiler/Tracer
    * ROCm Debugger

* Performance Tuning for HIP Programs
* HIPify - Going from CUDA to HIP

## HIP 300 Level (Advanced)

**Who are these courses for?**

* Experienced HIP developers

**Things covered in these courses**

* HIP/ROCm Libraries

    * rocBLAS
    * rocSPARSE
    * rocFFT
    * rocRAND

* Multi GPU Scaling

# HIP Courses

| **Legend** |
| --- |
| In-Person Course |
| Self Serve Video Course |
| Self Serve Documentation |

## 100 Level

| **Course Name** | **Topics Covered** | **Course Type** | **Avg Time to Complete** | **Prerequisites** | **Target Audience** |
| --- | --- | --- | --- | --- | --- |
| [**HIP 100: Fundamentals of HIP Programming**](https://amd.atlassian.net/wiki/x/UYCyHw) | Introduction to Programming in HIP; Data Parallelism; Host and Device; HIP Thread Hierarchy; HIP Programming Model; Enumerating Devices in HIP; Getting Device Properties in HIP and Programming Example - Vector Addition; HIP Memory Management, Allocation, Transfers; Launching Kernels and writing HIP Kernels; Error Handling; AMD GPU Compute Units; Block Execution; AMD GCN Computing Units; Static and Dynamic Shared Memory Syntax; Constant Memory Syntax; Shared Memory Explanation; HIP using ROCm Profiler: Matrix Transpose; Matrix Transpose: Naive Version; Matrix Transpose: Optimized LDS Version; Matrix Transpose: Key Takeaways; Debugging Tips and Tricks; Debugging Tips and Tricks - Wrap up | Video, Document - Slides and PDFs | ~3hrs | NA | Everyone |
| [**HIP 101: HIP Programming Part A**](https://amd.atlassian.net/wiki/x/ZI6yHw) | Vector Add in HIP (Assignment review); Compiling HIP on NVIDIA Systems; HIP Kernel Language; HIP Thread Hierarchy; HIP Memory Hierarchy; HIP Language Functions; Debugging; Printing from kernel; Querying Device and Runtime Features | Video, Document - Slides and Homework | ~2hrs | **Course 100** | All HIP Developers (New + Experienced) |
| [**HIP 102: HIP Programming Part B**](https://amd.atlassian.net/wiki/x/UIWyHw) | Matrix Transpose and Matrix Multiplication (previous homeworks); Thread Synchronization and Cooperation in HIP; Atomic Operations; Warp-level Operations; Intra-block Synchronization; Inter-block Synchronization; Example: Reduction; Concurrency and Overlapping Operations in HIP; HIP Streams; HIP Events; Explicit and implicit stream synchronization; Assignment: Histogram | Video, Document - Slides and Homework | ~2hrs | **Courses 100 to 101** | All HIP Developers (New + Experienced) |
| [**HIP 103: AMD GPU Architecture**](https://amd.atlassian.net/wiki/x/xoWyHw) | The evolution of AMD GPU architectures; GCN architecture; Kernel launching; Instruction execution; Memory hierarchy | Video, Document - Slides and Homework | ~1.5hrs | **Courses 100 to 102** | Everyone |

## 200 Level

| **Course Name** | **Topics Covered** | **Course Type** | **Avg Time to Complete** | **Prerequisites** | **Target Audience** |
| --- | --- | --- | --- | --- | --- |
| [**HIP 200: HIP Tools**](https://amd.atlassian.net/wiki/x/WY6yHw) | ROCm Info; ROCm SMI; ROCm Profiler/Tracer; ROCm Debugger | Video, Document - Slides and Homework | ~1.5hrs | **Courses 100 to 103** | All HIP Developers (New + Experienced) |
| [**HIP 201: Performance Tuning for HIP Programs**](https://amd.atlassian.net/wiki/x/bYSyHw) | How to tune HIP programs for optimized performance? | Video, Document - Slides | ~1.5hrs | **Courses 100 to 103, 200** | All HIP Developers (New + Experienced) |
| [**HIP 202: HIPify - CUDA to HIP**](https://amd.atlassian.net/wiki/x/aISyHw) | Introduction; Explore the hipify process; Discuss the motivation for hipifying CUDA programs; Show the code porting process, mapping CUDA to HIP using the HIP translation tools; Learn how to use hipify-perl and hipify-clang; 3 demos; Common cases that need manual porting; Converting a simple application; Porting a Deep Learning CUDA-CNN to HIP; Porting Machine Learning K-means to HIP; Wrap-up: Porting from CUDA to HIP | Video, Document - Slides and Labs | ~3hrs | **Courses 100 to 103, 200, 201** | All HIP Developers (New + Experienced) |
| [**HIP 203: HIP/ROCm Libraries A**](https://amd.atlassian.net/wiki/x/rIGyHw) | rocBLAS | Video, Document - Slides | ~1.5hrs | **Courses 100 to 103, 200 to 202** | All HIP Developers (New + Experienced) |
| [**HIP 204: HIP/ROCm Libraries B**](https://amd.atlassian.net/wiki/x/xrGyHw) | rocSparse; rocFFT; rocRAND | Video, Document - Slides | ~1.5hrs | **Courses 100 to 103, 200 to 203** | All HIP Developers (New + Experienced) |

## 300 Level

| **Course Name** | **Topics Covered** | **Course Type** | **Avg Time to Complete** | **Prerequisites** | **Target Audience** |
| --- | --- | --- | --- | --- | --- |
| [**HIP 300: Multi-GPU Scaling**](https://amd.atlassian.net/wiki/x/ZLCyHw) | HIP Device APIs; Stream-based multi-GPU programming; Thread-based multi-GPU programming; MPI-Based multi-GPU programming; GPU-GPU communication; ROCm Collective Communication Library (RCCL) | Video, Document - Slides | ~1.5 hrs | **Courses 100 to 103, 200 to 204** | Experienced HIP Developers |

# Additional Resources

* To provide feedback on HIP training or on the learning center in general, please go to [_**HIP FEEDBACK PAGE**_](https://amd.atlassian.net/wiki/x/CI6yHw)

---

# Descendant pages (full content)

The "HIP Training at AMD" page has the following child pages. The three section
container pages (`HIP at AMD: 100/200/300 Level`, pageIds `531807554`, `531804264`,
`531804266`) have **empty bodies** — they exist only to group the course pages — so
they are listed for completeness but have no content to reproduce.

## HIP 100: Fundamentals of HIP Programming

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531791953/HIP+100+Fundamentals+of+HIP+Programming
> **pageId:** `531791953` · version 32 (2025-04-06)

**Course Info**

### **Who is this course for?**

* Everyone at AMD

**What you will learn in this course?**

_Topics Covered:_

* Introduction to Programming in HIP

    * Data Parallelism
    * Host and Device
    * HIP Thread Hierarchy
    * HIP Programming Model
    * Enumerating Devices and in HIP
    * Getting Device Properties in HIP and Programming Example - Vector Addition
    * HIP Memory Management, Allocation, Transfers
    * Launching Kernels and writing HIP Kernels
    * Error Handling
    * AMD GPU Compute Units
    * Block Execution
    * AMD GCN Computing Units
    * Static and Dynamic Shared Memory Syntax
    * Constant Memory Syntax
    * Shared Memory Explanation

* HIP using ROCm Profiler: Matrix Transpose
* Matrix Transpose: Naive Version
* Matrix Transpose: Optimized LDS Version
* Matrix Transpose: Key Takeaways
* Debugging Tips and Tricks
* Debugging Tips and Tricks - Wrap up

### **Important Note: If the course video is broken on your end, use this link to access the videos -** [**https://syifan.notion.site/AMD-HIP-Training-Course-86cb772392dc45d9bc19f7018878505c**](https://syifan.notion.site/AMD-HIP-Training-Course-86cb772392dc45d9bc19f7018878505c)

### Introduction to Programming in HIP

### HIP using ROCm Profiler: Matrix Transpose

Learn about the profiler, a tool that can help determine the bottlenecks of an application and other characteristics, and its use in optimizations.

### Matrix Transpose: Naive Version

The Naïve Matrix Transpose is a basic transpose kernel that can achieve a fraction of the effective bandwidth of the copy kernel because of the way it reads data.

### Matrix Transpose: Optimized LDS Version

The Local Data Share is a user-managed cache available on AMD GPUs that enables data-sharing within threads of the same thread-block. It allows for 100x faster reads and writes than global memory and can optimize the naïve matrix transpose throughput.

### Matrix Transpose: Key Takeaways

### Debugging Tips and Tricks / Wrap up

### Homework 1 - Review of SLURM commands and your first HIP program.

Before the next course, complete the following activities:

* a.) Make sure you can login to the Penguin POD system.
* b.) Try out different SLURM commands to run programs both interactively and in batch mode. Also test commands that can check on the status of the system and your job. You can write a "helloworld" program or use the matrix-vector multiply code provided.
* c.) Using the matrix-vector multiply code provided, develop a HIP version of this code to run on the MI-50. You may want to play with the number of ROWS and COLUMNS, but be careful making them too large.

### HIP Program Files

* Please download this zip folder and find all the files you will need for the HIP courses:
* [**HIP Program files.zip**](https://amd.atlassian.net/wiki/download/attachments/531793018/HIP%20Program%20files.zip?version=1&modificationDate=1655231897390&api=v2)

### Next Steps and Additional Materials

* Use the **Course Breakdown** table found on the [_**HIP Training at AMD**_](https://amd.atlassian.net/wiki/x/P4CyHw) landing page to figure out which course you are _required_ to take next.

## HIP 101: HIP Programming Part A

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531795556/HIP+101+HIP+Programming+Part+A
> **pageId:** `531795556` · version 22 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* Vector Add in HIP (Assignment review)
* Compiling HIP on NVIDIA Systems
* HIP Kernel Language

    * HIP Thread Hierarchy
    * HIP Memory Hierarchy
    * HIP Language Functions

* Debugging

    * Printing from kernel

* Querying Device and Runtime Features

**Prerequisites:**

* [HIP 100: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw)

### Resources

* **CUDA Programming Guide:** [https://docs.nvidia.com/cuda/cuda-c-programming-guide/](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
* **HIP Programming Guide:** [https://sep5.readthedocs.io/en/latest/Programming_Guides/Programming-Guides.html](https://sep5.readthedocs.io/en/latest/Programming_Guides/Programming-Guides.html)

### Homework 2

**Matrix Transpose** — Write a program that transposes an input matrix out of place on the MI50. The program should take in a pointer to a two-dimensional matrix on the host, transfer it to device memory, perform the needed operations and transfer the results to host memory. The dimensions of the matrix are arbitrary, and not necessarily powers of 2. Be sure to compare the results of GPU and CPU transpose operations together, and try it out with different input sizes. As a bonus, try to optimize your kernel by using shared memory.

**Matrix Multiplication** — Building on last week's assignment, write a program that multiplies two matrices with appropriate dimensions together on the MI50, places them in a third matrix, and transfers them back to the host. The matrix dimensions must be arbitrary and not powers of two. Be sure to compare the results of your kernel with the CPU implementation, and try out different dimensions.

### Homework 1 Solutions

Please find the **matrixVectorMultiplycode.txt** file in the zip folder available on the [HIP 100: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw) course page.

## HIP 102: HIP Programming Part B

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531793232/HIP+102+HIP+Programming+Part+B
> **pageId:** `531793232` · version 18 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* Matrix Transpose and Matrix Multiplication (previous homeworks)
* Thread Synchronization and Cooperation in HIP

    * Atomic Operations
    * Warp-level Operations
    * Intra-block Synchronization
    * Inter-block Synchronization

* Example: Reduction
* Concurrency and Overlapping Operations in HIP

    * HIP Streams
    * HIP Events
    * Explicit and implicit stream synchronization

* Assignment: Histogram

**Prerequisites:**

* [HIP 101: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw)
* [HIP 102: HIP Programming Part A](https://amd.atlassian.net/wiki/x/ZI6yHw)

### Resources

* **CUDA Programming Guide:** [https://docs.nvidia.com/cuda/cuda-c-programming-guide/](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
* **HIP Programming Guide:** [https://sep5.readthedocs.io/en/latest/Programming_Guides/Programming-Guides.html](https://sep5.readthedocs.io/en/latest/Programming_Guides/Programming-Guides.html)

### Homework 3 — Histogram of a 1D Array

Write a HIP program of the normal C++ code below that calculates the histogram of a random 1D array. The range of the histogram for this assignment is equal to the minimum and maximum values present in the array of interest. The number of bins is arbitrary, and can cause the bin size to be a floating point number. Recall that the histogram's goal is to divide the range between the minimum and maximum values into equally-sized bins, and calculate the number of elements in the array that fall into each bin range. The output is an array with the size equal to the number of bins, and each element of the output array is the number of integers from the original array that fell into that bin. Assume that the minimum number of the bin is included while the maximum number is excluded; for example, number 1 falls into bin `[1, 3)`, but number 3 does not and falls into the next bin `[3, 5)`.

For this assignment, you are free to use any strategy you deem useful to parallelize the histogram calculation, as long as it gives the correct result. Taking advantage of the GPU memory hierarchy with proper thread coordination as discussed in class is encouraged, but not required; however, try to keep the GPU threads involved in the computation occupied as much as possible and minimize (atomic) writes to global memory.

```cpp
#include <iostream>
#include <vector>
#include <cmath>

// Size of the 1D array to calculate its histogram
#define SIZE 1000
// Number of bins for the histogram
#define NUM_BINS 9
// Minimum integer present in the 1D array; also the minimum range of the histogram
#define MIN_RAND_INT 0
// Maximum integer present in the 1D array; also the maximum range of the histogram
#define MAX_RAND_INT 100

// Initializes a std::vector with random values between min_rand_int and max_rand_int
void initialize_vector(std::vector<int>& vec, int min_rand_int, int max_rand_int) {
    for (int & el : vec)
        el = rand() % max_rand_int + min_rand_int;
}

// A friendly function overload for printing the contents of a vector (for debugging)
std::ostream& operator<<(std::ostream& os, const std::vector<int>& vec) {
    os << "[ ";
    for (int el : vec)
        os << el << ", ";
    os << "]\n";
    return os;
}

// Calculates the histogram of the vector, based on the number of bins, minimum and maximum range given.
std::vector<int> calculate_histogram(const std::vector<int>& vec, int num_bins, int min_value, int max_value) {
    // Calculate the bin length of the histogram. It can be a floating point.
    float bin_size = static_cast<float>(max_value - min_value) / static_cast<float>(num_bins);
    // Where we keep track of the histogram bins
    std::vector<int> bin_stats(num_bins, 0);
    // To find out where the number falls, we normalize the number between 0 and max_value - min_value,
    // then divide by bin_size to determine which bin it falls into
    for (int el: vec)
        bin_stats[std::floor(static_cast<float>(el - min_value) / bin_size)] += 1;
    return bin_stats;
}

// Helper function to print the contents of the histogram
void print_histogram(const std::vector<int>& vec, int min_value, int max_value) {
    float bin_size = static_cast<float>(max_value - min_value) / static_cast<float>(vec.size());
    for (int i = 0; i < vec.size(); i++) {
        float bin_min = static_cast<float>(i) * bin_size + static_cast<float>(min_value);
        float bin_max = bin_min + bin_size;
        std::cout << "[" << bin_min << ", " << bin_max << "): " << vec[i] << std::endl;
    }
}

int main() {
    // Fix the seed for reproducibility, hence the array content will be the same across each run
    srand(0);
    // Initialize the array with "random" content
    std::vector<int> array(SIZE);
    initialize_vector(array, MIN_RAND_INT, MAX_RAND_INT);
    // Print the array contents before calculating its histogram
    std::cout << "Array contents:" << std::endl;
    std::cout << array;
    // Calculate the histogram of the array
    auto histogram = calculate_histogram(array, NUM_BINS, MIN_RAND_INT, MAX_RAND_INT);
    // Print the histogram
    std::cout << "Histogram:" << std::endl;
    print_histogram(histogram, MIN_RAND_INT, MAX_RAND_INT);
    return 0;
}
```

### Homework 2 Solutions

Please find the **matrixMultiply.txt** file in the zip folder available on the [HIP 100: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw) course page.

## HIP 103: AMD GPU Architecture

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531793350/HIP+103+AMD+GPU+Architecture
> **pageId:** `531793350` · version 20 (2025-04-06)

**Course Info**

**Who is this course for?**

* Everyone at AMD

**What you will learn in this course?**

_Topics Covered:_

* The evolution of AMD GPU architectures
* GCN architecture
* Kernel launching
* Instruction execution
* Memory hierarchy

**Prerequisites:**

* [HIP 100: Introduction to the HIP/ROCm Training](https://amd.atlassian.net/wiki/x/eoSyHw)
* [HIP 101: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw)
* [HIP 102: HIP Programming Part A](https://amd.atlassian.net/wiki/x/ZI6yHw)
* [HIP 103: HIP Programming Part B](https://amd.atlassian.net/wiki/x/UIWyHw)

### Homework 4: Exploring Memory Coalescing

Two simple vector addition programs are provided (find **vadd_v1.cu.txt** and **vadd.cu.txt** in the zip folder on the [HIP 100](https://amd.atlassian.net/wiki/x/UYCyHw) course page):

* The input argument is the size of the vector.
* Run these two programs, starting with a large vector size (e.g., 10,000,000 elements), and increase the size.
* Compare the execution times of the two programs while using the same input.
* Why does one program run faster than the other?

### Homework 3 Solution

Please find the **histogram_solution.txt** file in the zip folder available on the [HIP 100: Fundamentals of HIP Programming](https://amd.atlassian.net/wiki/x/UYCyHw) course page.

## HIP 200: HIP Tools

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531795545/HIP+200+HIP+Tools
> **pageId:** `531795545` · version 12 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* ROCm Info
* ROCm SMI
* ROCm Profiler/Tracer
* ROCm Debugger

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)

### Homework 5

**Problem 1** — Profile your **Matrix Transpose** program (the assignment from unit 2) using both the API tracing mode and the performance counter mode. Answer the following:

* What is the ratio between memory copy and kernel execution time?
* How much data is read from the GPU main memory and how much data is written into the GPU main memory?

**Problem 2** — Debug the Matrix Transpose program written as the assignment of unit 2. Tune the problem size down to a level where you only need 1-2 wavefronts. Set a break point in the GPU kernel. Run the program so that the debugger stops at the breakpoint you set in the kernel. List both the HIP code and the assembly of the kernel on your screen, and use the "step over" command to check how the HIP program maps to the assembly.

## HIP 201: Performance Tuning for HIP Programs

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531793005/HIP+201+Performance+Tuning+for+HIP+Programs
> **pageId:** `531793005` · version 11 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* How to tune HIP programs for optimized performance?

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)
* [HIP 200: HIP Tools](https://amd.atlassian.net/wiki/x/WY6yHw)

_(Body is otherwise course video + slides embedded as Confluence media, not fetchable.)_

## HIP 202: HIPify and CUDA to HIP

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531793000/HIP+202+HIPify+and+CUDA+to+HIP
> **pageId:** `531793000` · version 16 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* Introduction
* Explore the hipify process

    * Discuss the motivation for hipifying CUDA programs
    * Show the code porting process, mapping CUDA to HIP using the HIP translation tools

* Learn how to use hipify-perl and hipify-clang tool to enhance the hipify process (3 demos)
* Discuss some common cases that need manual porting
* Converting a simple application
* Porting a Deep Learning CUDA-CNN to HIP
* Porting Machine Learning K-means to HIP
* Wrap-up: Porting from CUDA to HIP

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)
* [HIP 200: HIP Tools](https://amd.atlassian.net/wiki/x/WY6yHw)
* [HIP 201: Performance Tuning for HIP Programs](https://amd.atlassian.net/wiki/x/bYSyHw)

The course is structured into demo segments — "Converting a simple application", "Porting Deep Learning CUDA-CNN to HIP", "Porting Machine Learning K-means to HIP", and "Wrap-up: Porting from CUDA to HIP" — each with an associated video and lab (embedded media, not fetchable).

## HIP 203: HIP/ROCm Libraries A

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531792300/HIP+203+HIP+ROCm+Libraries+A
> **pageId:** `531792300` · version 14 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* rocBLAS

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)
* [HIP 200: HIP Tools](https://amd.atlassian.net/wiki/x/WY6yHw)
* [HIP 201: Performance Tuning for HIP Programs](https://amd.atlassian.net/wiki/x/bYSyHw)
* [HIP 202: HIPify and CUDA to HIP](https://amd.atlassian.net/wiki/x/aISyHw)

## HIP 204: HIP/ROCm Libraries B

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531804614/HIP+204+HIP+ROCm+Libraries+B
> **pageId:** `531804614` · version 12 (2025-04-06)

**Course Info**

**Who is this course for?**

* All HIP Developers (New + Experienced)

**What you will learn in this course?**

_Topics Covered:_

* rocSparse
* rocFFT
* rocRAND

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)
* [HIP 200: HIP Tools](https://amd.atlassian.net/wiki/x/WY6yHw)
* [HIP 201: Performance Tuning for HIP Programs](https://amd.atlassian.net/wiki/x/bYSyHw)
* [HIP 202: HIPify and CUDA to HIP](https://amd.atlassian.net/wiki/x/aISyHw)
* [HIP 203: HIP/ROCm Libraries A](https://amd.atlassian.net/wiki/x/rIGyHw)

## HIP 300: Multi-GPU Scaling

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531804260/HIP+300+Multi-GPU+Scaling
> **pageId:** `531804260` · version 15 (2025-04-06)

**Course Info**

**SME:** @Former user (Deleted), @Former user (Deleted)

**Who is this course for?**

* Experienced HIP Developers

**What you will learn in this course?**

_Topics Covered:_

* HIP Device APIs
* Stream-based multi-GPU programming
* Thread-based multi-GPU programming
* MPI-Based multi-GPU programming
* GPU-GPU communication
* ROCm Collective Communication Library (RCCL)

**Prerequisites:**

* [HIP at AMD: 100 Level](https://amd.atlassian.net/wiki/x/Qr2yHw)
* [HIP at AMD: 200 Level](https://amd.atlassian.net/wiki/x/aLCyHw)

### Next Steps and Additional Materials

Having reached the end of this course, you have reached the end of the AMD HIP training materials and should now be comfortable using and writing HIP Programs.

* Use the **Points of Contact** table on the [_**HIP Training at AMD**_](https://amd.atlassian.net/wiki/x/P4CyHw) main page to find a subject matter expert who can help you find more material on a HIP topic of interest.

## HIP FEEDBACK PAGE

> **URL:** https://amd.atlassian.net/wiki/spaces/LC/pages/531795464/HIP+FEEDBACK+PAGE
> **pageId:** `531795464` · version 2 (2022-06-27)

**Instructions**

## **This page is dedicated for capturing any feedback on the HIP Training.**

* You have two components here:

    * Feedback Survey: Please use the following link to submit your feedback - [**Learning Centre Feedback**](https://forms.office.com/Pages/ResponsePage.aspx?id=H5bYPYjkYE6OEagtmU4YPTHtAxSuQsVBsptdy__xJAJUQU81NEpQVk40MkM5Uk8wUVQ2WFNKT0YyVS4u)
    * Feedback Table: The table below will be used to capture feedback from the forms and make it available for everyone to view. One can use this table to see different feedback and avoid submitting redundant feedback.

| **Feedback** | **Reviewed by the Subject Matter Experts** | **Comments** | **Action Items** | **Target resolution** |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Empty container pages (no body content)

* **HIP at AMD: 100 Level** — pageId `531807554` — https://amd.atlassian.net/wiki/spaces/LC/pages/531807554/HIP+at+AMD+100+Level
* **HIP at AMD: 200 Level** — pageId `531804264` — https://amd.atlassian.net/wiki/spaces/LC/pages/531804264/HIP+at+AMD+200+Level
* **HIP at AMD: 300 Level** — pageId `531804266` — https://amd.atlassian.net/wiki/spaces/LC/pages/531804266/HIP+at+AMD+300+Level
