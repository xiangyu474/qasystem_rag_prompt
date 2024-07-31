import logging

# 创建一个日志记录器
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)  # 设置日志级别为INFO

# 创建一个控制台处理器并设置级别为INFO
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 创建一个格式器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 将格式器添加到处理器
ch.setFormatter(formatter)

# 将处理器添加到日志记录器
logger.addHandler(ch)

# 在代码中使用自定义的日志记录器
logger.info("Client is ready.")
for i in range(10):
    logger.info(f"Inserted {i + 1} documents so far.")
    logging.error("Client is not ready.")