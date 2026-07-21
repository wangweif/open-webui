import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getOAuthClientInfo = async (clientId: string) => {
	let error = null;

	const res = await fetch(`/oauth/client-info/${clientId}`, {
		method: 'GET',
		headers: { 'Content-Type': 'application/json' }
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

	if (error) throw error;
	return res;
};

export const postOAuthConsent = async (token: string, body: {
	client_id: string;
	redirect_uri: string;
	scope: string;
	state?: string;
	response_type: string;
}) => {
	let error = null;

	const res = await fetch(`/oauth/authorize/consent`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
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

	if (error) throw error;
	return res;
};

// ─── 客户端管理 API ──────────────────────────────────────

export const getOAuthClients = async (token: string) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients`, {
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
	if (error) throw error;
	return res;
};

export const createOAuthClient = async (token: string, body: {
	client_id: string;
	client_name: string;
	redirect_uris: string;
	grant_types?: string;
	scope?: string;
}) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
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
	if (error) throw error;
	return res;
};

export const getOAuthClient = async (token: string, clientId: string) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients/${clientId}`, {
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
	if (error) throw error;
	return res;
};

export const updateOAuthClient = async (token: string, clientId: string, body: {
	client_name?: string;
	redirect_uris?: string;
	grant_types?: string;
	scope?: string;
	status?: string;
}) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients/${clientId}/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
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
	if (error) throw error;
	return res;
};

export const deleteOAuthClient = async (token: string, clientId: string) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients/${clientId}`, {
		method: 'DELETE',
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
	if (error) throw error;
	return res;
};

export const resetOAuthClientSecret = async (token: string, clientId: string) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/oauth/clients/${clientId}/reset-secret`, {
		method: 'POST',
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
	if (error) throw error;
	return res;
};
