# BandwidthTest

Current BandwidthTest.cpp program records initial synchronization time, file loading time and the time between head tracking events for each node. Data are collected and recorded in the txt file cave0xx: /tmp/cave0xx-evlog.txt. Steps on data merging and analysis are explained in later section of this document.

## Getting Started with data collection

#### Download Repository

    ```
    git clone https://github.com/tsgouros/cave-utils.git
    cd yurt
    ```
  
#### Configure and build

    ```
    cd src
    make
    ```
    

#### Run Command

    ```
    ./run
    ```



## Getting Started with data analysis

The data files collected in the previous step are sparsely distributed at each cave node. We first need to merge all the files into one:

#### Data Merge

    ```
    cd bin
    bash bandwidth-merge.sh
    ```
This will generate the ```combined.txt``` file at /yurt/doc/BandwidthTest/performance/data/combined.txt


#### Data Analysis

    ```
    (assuming still in the bin dir)
    python bandwidth-analyze.py
    ```
This will generate the ```time-analysis.txt``` file at /yurt/doc/BandwidthTest/performance/time-analysis.txt. The document will contain average, minimum, maximum and standard deviation of the interested parameters measured.






