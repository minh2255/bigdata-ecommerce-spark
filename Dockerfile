FROM apache/spark:3.5.9-java17-python3

USER root
RUN pip3 install --no-cache-dir pandas pyarrow matplotlib
# Nếu build báo "externally-managed-environment", đổi dòng trên thành:
# RUN pip3 install --no-cache-dir --break-system-packages pandas pyarrow matplotlib
USER spark
