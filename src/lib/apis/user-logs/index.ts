import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface UserLogEntry {
	id: string;
	type: 'login' | 'page_view';
	user_id?: string;
	user_name?: string;
	user_email?: string;
	action: string;
	details?: {
		[key: string]: any;
	};
	ip_address?: string;
	user_agent?: string;
	created_at: number;
}

export interface UserLogsResponse {
	logs: UserLogEntry[];
	total: number;
	page: number;
	limit: number;
}

export interface LogType {
	value: string;
	label: string;
}

export const getAllUserLogs = async (
	token: string,
	page: number = 1,
	limit: number = 20,
	logType?: string,
	userId?: string,
	startTime?: number,
	endTime?: number
): Promise<UserLogsResponse> => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('page', `${page}`);
	searchParams.append('limit', `${limit}`);
	if (logType) {
		searchParams.append('log_type', logType);
	}
	if (userId) {
		searchParams.append('user_id', userId);
	}
	if (startTime) {
		searchParams.append('start_time', `${startTime}`);
	}
	if (endTime) {
		searchParams.append('end_time', `${endTime}`);
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/user-logs/all?${searchParams.toString()}`, {
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
			error = err.detail || err.message;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ?? { logs: [], total: 0, page: 1, limit: 20 };
};

export const getLogTypes = async (token: string): Promise<{ types: LogType[] }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/user-logs/types`, {
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
			error = err.detail || err.message;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ?? { types: [] };
};

