"""提示词管理模块 - 支持模板加载和变量替换"""

from pathlib import Path
from typing  import Dict, Optional

class PromptManager:
    """提示词模板管理器"""
    
    # 可用的提示词模板
    TEMPLATES = {
        "detailed": "code_analysis.txt",    # 详细分析(默认)
        "concise":  "code_analysis_concise.txt",  # 简洁版
        "performance": "code_analysis_performance.txt" # 性能优化
    }
    
    def __init__(self,  prompts_dir: str = "prompts"):
        """初始化提示词管理器

        Args:
            prompts_dir: 提示词模板目录
        """
        self.prompts_dir = Path(prompts_dir)

        # 验证目录存在
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"提示词目录不存在: {self.prompts_dir}\n"
                "请确保 prompts/ 目录已创建"
            )
            
    def load_template(self, template_name: str = "detailed") -> str:
        """加载提示词模板
        
        Args:
            template_name: 模板名称(deltailed/concise/performance)
            
        Return:
            模板内容
            
        Raise:
            ValueErrorr: 模板名称无效
            FileNotFoundError: 模板文件不存在
        """
        # 验证模板名称
        if template_name not in self.TEMPLATES:
            available = ",".join(self.TEMPLATES.keys())
            raise ValueError(
                f"无效的模板名称: {template_name}\n"
                f"可用模板: {available}"
            )
            
        # 加载模板文件
        template_file = self.prompts_dir / self.TEMPLATES[template_name]
        
        if not template_file.exists():
            raise FileNotFoundError(
                f"模板文件不存在: {template_file}\n"
                f"请确保文件已创建"
            )
            
        return template_file.read_text(encoding="utf-8")
    
    def build_prompt(
        self,
        template_name: str,
        code: str,
        file_path: str,
        line_range: Optional[str] = None
    ) -> str:
        """构建完整提示词

        Args:
            template_name (str): 模板名称
            code (str): 代码内容
            file_path (str): 文件路径
            line_range (Optional[str], optional): 行范围(可选)

        Returns:
            填充变量后的完整提示词
        """
        # 加载模板
        template = self.load_template(template_name)

        # 构建位置信息
        location = f"{file_path}"
        if line_range:
            location += f"(第 {line_range} 行)"

        # 替换模板变量
        prompt = template.format(
            location=location,
            code=code
        )
        
        return prompt
    
    @classmethod
    def list_templates(cls) -> Dict[str, str]:
        """列出所有可用模板
        
        Return:
            {模板名: 描述} 字典
        """
        return {
            "detailed": "详细分析 - 系统化深度分析（功能/逻辑/问题/建议）",
            "concise": "简洁模式 - 快速总结核心问题和建议",
            "performance": "性能优化 - 专注于性能瓶颈和优化方案"
        }
        
# 测试代码
if __name__ == "__main__":
    try:
        pm = PromptManager()
        
        print("✅ 提示词管理器初始化成功\n")
        print("📋 可用模板:")
        for name, desc in PromptManager.list_templates().items():
            print(f"  • {name}: {desc}")
            
        # 测试加载
        print("\n🧪 测试加载 detailed 模板...")
        template = pm.load_template("detailed")
        print(f"✅ 模板长度: {len(template)} 字符")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        