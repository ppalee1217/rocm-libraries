docker run -it -d --device=/dev/kfd --device=/dev/dri \
            --security-opt seccomp=unconfined \
            -v /data1/perlee:/src \
            --name perlee \
            registry-sc-harbor.amd.com/rocm-ci-images/compute-rocm-rel-7.2:93-ubuntu-24.04

docker exec -it perlee /bin/bash