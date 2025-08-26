import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface KnowledgeBase {
	kb_id: string;
	kb_name: string;
	enabled: boolean;
}

export interface AssistantInfo {
	assistant_id: string;
	kb_ids: string[];
	knowledge_bases: KnowledgeBase[];
	tavily_api_key?: string;
	tavily_enabled: boolean;
	reasoning_enabled: boolean;
}

export interface UpdateKnowledgeBaseRequest {
	assistant_id: string;
	kb_ids: string[];
}

export interface UpdateTavilyRequest {
	assistant_id: string;
	tavily_enabled: boolean;
}

export interface UpdateReasoningRequest {
	assistant_id: string;
	reasoning_enabled: boolean;
}

/**
 * 获取assistant的知识库信息
 */
export const getAssistantKnowledgeBases = async (
	token: string,
	assistantId: string
): Promise<AssistantInfo> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/ragflow/assistant/${assistantId}/knowledge-bases`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 根据模型ID获取知识库信息
 */
export const getModelKnowledgeBases = async (
	token: string,
	modelId: string
): Promise<AssistantInfo> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/ragflow/model/${modelId}/knowledge-bases`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 更新assistant的知识库配置
 */
export const updateAssistantKnowledgeBases = async (
	token: string,
	requestData: UpdateKnowledgeBaseRequest
): Promise<{ success: boolean; message: string }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/ragflow/assistant/update-knowledge-bases`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(requestData)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 获取assistant的完整信息，包括知识库和tavily配置
 */
export const getAssistantInfo = async (
	token: string,
	assistantId: string
): Promise<AssistantInfo> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/ragflow/assistant/${assistantId}/info`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 更新assistant的tavily搜索配置
 */
export const updateAssistantTavily = async (
	token: string,
	request: UpdateTavilyRequest
): Promise<{ success: boolean; message: string }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/ragflow/assistant/update-tavily`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 更新assistant的推理配置
 */
export const updateAssistantReasoning = async (
	token: string,
	request: UpdateReasoningRequest
): Promise<{ success: boolean; message: string }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/ragflow/assistant/update-reasoning`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}; 