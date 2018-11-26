#!/bin/bash

FIO_NUM_THREADS="1 2 4 8"
TIME=240
HOME=/home/ubuntu
DATE=$(date +%F_%H-%M-%S)
echo "##############################################"
echo "Starting at: ${DATE}"
echo "##############################################"
TESTDIR=$HOME/tests_${DATE}/fio-3.1
WORKDIR=$TESTDIR/results
LOAD=0
# UNBUFFERED=1
BUFFERED=1
NRFILES=4
echo "$DATE"
TEST=BEEGFS-all-master-node
 
RESULTSDIR=${WORKDIR}/$TEST
 
EXEC=fio
ENGINE=psync
for threads in $FIO_NUM_THREADS
do
    #####################################################################
    TMPD="/mnt/openhpc/pxh/fio-tests/ /mnt/ssdnode/pxh/fio-tests/ /mnt/nvmenode/pxh/fio-tests/"
    FS="1G 2G 4G"
    BS="16k 64k 128k 512k 1024k"
    #####################################################################
    for TMPDIR in $TMPD
    do
        sleep 20
        BEEGFS_CLUSTER=`echo $TMPDIR | cut  -d '/' -f 3`
        for FILE_SIZE in $FS
        do
            if [ ! -d $RESULTSDIR ]; then
                echo "making test_directory ($RESULTSDIR)."
                mkdir -p $RESULTSDIR
            fi
            cd $RESULTSDIR
            if [ ! -d $TMPDIR ]; then
                echo "making test_directory ($TMPDIR)."
                mkdir -p $TMPDIR 
            fi
            rm -f $TMPDIR/*
             
            for BLOCKSIZE in $BS
            do
                for RW in 0 1
                do
                    if [ $RW = 1 ]; then
                    ######################## WRITE PHASE##################################
                        RW_STEP_NAME="write"
                        read="0"
                        write="100"
                    else
                    ######################## READ PHASE##################################
                        RW_STEP_NAME="read"
                        read="100"
                        write="0"
                    fi
                    ########################BUFFERED PHASE##################################
                    if [ $BUFFERED = 1 ]; then
                        BUFFER_STEP_NAME="buffered"
                        echo "Result file prefix: ${FILE_OUT}"
                        DIRECT="0"
                    else
                    ########################NON-BUFFERED PHASE##################################
                        BUFFER_STEP_NAME="unbuffered"
                        DIRECT="1\nrefill_buffers\n"
                    fi
                    echo "$BUFFER_STEP_NAME Block_size = $BLOCKSIZE dir = $TMPDIR file_size = $FILE_SIZE threads=$threads $DATE"
                    FILE_OUT=$RESULTSDIR/fio-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-${BUFFER_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}
                    echo "Result file prefix: ${FILE_OUT}"
                    cat <<EOJOB | $EXEC --idle-prof=system - > >(tee -a ${FILE_OUT}.log) 2> >(tee -a ${FILE_OUT}.stderr.log >&2)
[global]
directory=$TMPDIR
direct=$DIRECT
rw=readwrite
rwmixread=$read
rwmixwrite=$write
# blocksize split of 20% 4k, 16k, 256k and 1024k
#bssplit=4k/1:16k/5:64k/2:256k/2:1M/90
bs=$BLOCKSIZE
per_job_logs=0
#refill_buffers
invalidate=1
fsync_on_close=1
randrepeat=1
norandommap
#randrepeat=0
ioengine=$ENGINE
group_reporting
runtime=$TIME
time_based

[fio-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-${BUFFER_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}]
nrfiles=$NRFILES
filesize=$FILE_SIZE
numjobs=$threads
name=fio-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-${BUFFER_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}
write_bw_log=${BUFFER_STEP_NAME}-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}-${RW_STEP_NAME}.results
write_iops_log=${BUFFER_STEP_NAME}-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}-${RW_STEP_NAME}.results
write_lat_log=${BUFFER_STEP_NAME}-${BEEGFS_CLUSTER}-${RW_STEP_NAME}-block_${BLOCKSIZE}-size_${FILE_SIZE}-threads_${threads}-${RW_STEP_NAME}.results

EOJOB
                    sleep 20
                done
                sleep 20
            done
            sleep 20
        done
        sleep 20
    done
done
DATE=$(date +%F_%H-%M-%S)
echo "##############################################"
echo "Finishing at: ${DATE}"
echo "##############################################"

