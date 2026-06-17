# ========================================
# 配置文件 - 存放 API 密钥和参数
# ========================================

# Stability AI API Key
# 从 https://platform.stabilityai.com/ 获取
STABILITY_API_KEY = "YOUR_API_KEY_HERE"

# API 端点
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

# 图像生成参数
IMAGE_WIDTH = 512      # 图像宽度 (512, 576, 640, 704, 768, 832, 896, 960, 1024)
IMAGE_HEIGHT = 512     # 图像高度 (512, 576, 640, 704, 768, 832, 896, 960, 1024)
STEPS = 30             # 生成步数 (10-50)，步数越多质量越好但速度越慢
SCALE = 7.5            # 提示词引导尺度 (0-20)

# 输出目录
OUTPUT_DIR = "outputs"
