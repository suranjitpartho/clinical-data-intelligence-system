import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useConfig() {
  const [modelName, setModelName] = useState("Loading...");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [availableModels, setAvailableModels] = useState([]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const [configRes, modelsRes] = await Promise.all([
          api.get('/config'),
          api.get('/models')
        ]);
        setAvailableModels(modelsRes.data);
        const currentModel = modelsRes.data.find(m => m.id === configRes.data.model_name);
        setModelName(currentModel ? currentModel.name : configRes.data.model_name);
        setSelectedModel(configRes.data.model_name);
        setSelectedProvider(configRes.data.provider);
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };
    fetchConfig();
  }, []);

  return {
    modelName,
    setModelName,
    selectedModel,
    setSelectedModel,
    selectedProvider,
    setSelectedProvider,
    availableModels,
  };
}
