from langchain_openai import ChatOpenAI
import json
from langchain_ollama import OllamaEmbeddings

class ModelManager:
    def __init__(self, temperature=0.3):
        self.temperature = temperature
        self.config_path = "config.json"  # 配置文件路径
        self.model_config = self.load_config(self.config_path)

        self.llm_models = self.model_config.get("llm_models", {})
        self.models = list(self.llm_models.keys()) # 提取所有支持的模型名称
        self.current_model = self.models[0]  # 默认选第一个模型
        self._update_llm_config()
        self.llm = self._create_llm()#self.current_model
        self.embeddings = self._create_embeddings()

    def _validate_models(self):
        if not self.models:
            raise ValueError("配置文件中未找到LLM模型配置")
    def load_config(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载配置文件出错: {e}")
            return {}
    def _update_llm_config(self):
        config = self.llm_models[self.current_model]
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")            

    def _create_llm(self):#, model_name
        """创建 ChatOpenAI 实例"""
        return ChatOpenAI(
            model=self.current_model,
            temperature=self.temperature,
            streaming=True,
            api_key=self.api_key,
            base_url=self.base_url
        )
    def _create_embeddings(self):
        embed_config = self.model_config.get("embedding_model")
        return OllamaEmbeddings(**embed_config)

    def get_models(self):
        return self.models

    def get_current_model(self):
        return self.current_model

    def get_llm(self):
        return self.llm

    def switch_model(self, selected_model):
        """切换模型并更新 API 配置"""
        if selected_model not in self.models:
            raise ValueError(f"Model '{selected_model}' is not available.")
        
        # 更新当前模型
        self.current_model = selected_model
        self._update_llm_config()  # 调用统一的配置更新方法
        # 重新创建 LLM 实例
        self.llm = self._create_llm()