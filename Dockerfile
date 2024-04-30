FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装您的应用程序需要的其他依赖项
RUN apt-get update && apt-get install -y \
    python3-pip build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# 安装ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

ARG LIBRARY="-i https://pypi.tuna.tsinghua.edu.cn/simple"

COPY requirements.txt /workspace

RUN pip install --upgrade cython ${LIBRARY}
RUN pip install numpy==1.23.1
RUN pip install -r requirements.txt
RUN python3 -m pip install paddlepaddle-gpu==2.4.2.post117 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
RUN pip install torch==2.1.0 torchvision==0.16.0+cu118 --index-url https://download.pytorch.org/whl/cu118

COPY . /workspace

EXPOSE 8090

# 指定容器启动时执行的命令
CMD ["python3", "backend/flask_app.py"]