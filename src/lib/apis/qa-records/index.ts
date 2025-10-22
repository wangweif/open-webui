import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface AttachmentInfo {
	name?: string;
	type: 'file' | 'image';
	id?: string;
	url?: string;
	content?: string;
	size?: number;
	content_type?: string;
}

export interface QARecord {
	id: string;
	question: string;
	answer: string;
	user_name: string;
	user_email: string;
	user_id: string;
	attachments: AttachmentInfo[];
	created_at: number;
	updated_at: number;
	model: string;
	chat_id?: string;
}

export const getAllQARecords = async (token: string): Promise<QARecord[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/qa-records/all`, {
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
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ?? [];
};

export const getQARecordById = async (token: string, id: string): Promise<QARecord | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/qa-records/${id}`, {
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
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getQARecordsByUserId = async (
	token: string,
	userId: string
): Promise<QARecord[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/qa-records/user/${userId}`, {
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
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ?? [];
};

export const searchQARecords = async (
	token: string,
	query: string = '',
	page: number = 1,
	limit: number = 20,
	sortBy: string = 'created_at',
	sortOrder: string = 'desc'
): Promise<{ records: QARecord[]; total: number }> => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('query', query);
	searchParams.append('page', `${page}`);
	searchParams.append('limit', `${limit}`);
	searchParams.append('sort_by', sortBy);
	searchParams.append('sort_order', sortOrder);

	const res = await fetch(`${WEBUI_API_BASE_URL}/qa-records/search?${searchParams.toString()}`, {
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
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ?? { records: [], total: 0 };
};


