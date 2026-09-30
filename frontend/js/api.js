// Common API Helper for E-Healthcare Platform
const API = {
    BASE_URL: '',

    getToken() {
        return localStorage.getItem('ehealth_token');
    },

    setToken(token) {
        localStorage.setItem('ehealth_token', token);
    },

    getUser() {
        const u = localStorage.getItem('ehealth_user');
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem('ehealth_user', JSON.stringify(user));
    },

    clearAuth() {
        localStorage.removeItem('ehealth_token');
        localStorage.removeItem('ehealth_user');
    },

    authHeaders() {
        const token = this.getToken();
        const headers = {
            'Bypass-Tunnel-Reminder': 'true',
            'bypass-tunnel-reminder': '1'
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const headers = {
            ...this.authHeaders(),
            ...(options.headers || {})
        };

        if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        try {
            const res = await fetch(url, { ...options, headers });
            if (res.status === 401) {
                // Unauthorized token
                this.clearAuth();
                if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
                    window.location.href = '/';
                }
                throw new Error("Session expired. Please log in again.");
            }

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                const message = data.detail || (Array.isArray(data.detail) ? data.detail[0].msg : "Request failed");
                throw new Error(message);
            }
            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, { method: 'POST', body });
    },

    put(endpoint, body) {
        return this.request(endpoint, { method: 'PUT', body });
    },


    postForm(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            // fetch automatically sets correct multipart/form-data boundary
            headers: this.authHeaders()
        });
    },

    async login(email, password) {
        const res = await this.post('/api/auth/login', { email, password });
        this.setToken(res.access_token);
        this.setUser(res.user);
        return res;
    },

    async register(data) {
        const res = await this.post('/api/auth/register', data);
        this.setToken(res.access_token);
        this.setUser(res.user);
        return res;
    },

    logout() {
        this.clearAuth();
        window.location.href = '/';
    }
};
