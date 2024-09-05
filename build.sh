# 清理构建的临时文件
rm -rf build
rm -rf dist
rm -rf *.egg-info

echo "========================================================"
echo "build temp files removed"
echo "========================================================"

# Python工程构建打包
python3 setup.py sdist --formats=gztar
echo "========================================================"
echo "Python package success"
echo "========================================================"

APP_VERSION=1.0.0

docker build --pull \
    --network=host \
    --build-arg APP_VERSION=$APP_VERSION \
    -t llm-rag:$APP_VERSION \
    -f APP-META/Dockerfile .
