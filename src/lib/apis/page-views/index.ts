import { WEBUI_API_BASE_URL } from '$lib/constants';

//////////////
// 类型定义
//////////////

export interface PageViewCreateForm {
  url: string;
  access_type?: string;
}

export interface PageViewModel {
  id: number;
  url: string;
  user_id?: string;
  ip_address: string;
  user_agent?: string;
  referer?: string;
  access_type?: string;
  created_at: number;
}

export interface PageViewStatsResponse {
  url: string;
  view_count: number;
  first_view_at: number;
  last_view_at: number;
}

export interface AnalyticsSummary {
  total_views: number;
  unique_pages: number;
  top_pages: PageViewStatsResponse[];
  access_type_statistics: Record<string, number>;
}

//////////////
// API 函数
//////////////

/**
 * 记录登录用户的页面访问
 */
export const recordPageView = async (
  token: string,
  data: PageViewCreateForm
): Promise<{ message: string; id: number }> => {
  const response = await fetch(`${WEBUI_API_BASE_URL}/page-views/record`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      Cookie: `token=${token}`
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '记录页面访问失败');
  }

  return await response.json();
};

/**
 * 获取特定页面的访问统计
 */
export const getPageStats = async (
  token: string,
  url: string
): Promise<PageViewStatsResponse> => {
  const encodedUrl = encodeURIComponent(url);
  const response = await fetch(`${WEBUI_API_BASE_URL}/page-views/stats/${encodedUrl}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取页面统计失败');
  }

  return await response.json();
};

/**
 * 获取所有页面的访问统计（管理员）
 */
export const getPageViewStats = async (
  token: string,
  params: {
    skip?: number;
    limit?: number;
    order_by?: 'view_count' | 'last_view_at' | 'url';
  } = {}
): Promise<PageViewStatsResponse[]> => {
  const searchParams = new URLSearchParams();
  if (params.skip !== undefined) searchParams.set('skip', params.skip.toString());
  if (params.limit !== undefined) searchParams.set('limit', params.limit.toString());
  if (params.order_by) searchParams.set('order_by', params.order_by);

  const response = await fetch(`${WEBUI_API_BASE_URL}/page-views/stats?${searchParams}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取页面统计失败');
  }

  return await response.json();
};

/**
 * 获取分析摘要（管理员）
 */
export const getAnalyticsSummary = async (token: string): Promise<AnalyticsSummary> => {
  const response = await fetch(`${WEBUI_API_BASE_URL}/page-views/analytics/summary`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取分析摘要失败');
  }

  return await response.json();
};

/**
 * 获取访问类型统计（管理员）
 */
export const getAccessTypeStatistics = async (token: string): Promise<Record<string, number>> => {
  const response = await fetch(`${WEBUI_API_BASE_URL}/page-views/analytics/access-types`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取访问类型统计失败');
  }

  return await response.json();
};

//////////////
// 辅助函数
//////////////

/**
 * 根据URL路径推断访问类型
 */
export const inferAccessType = (url: string): string => {
  const path = url.toLowerCase();
  
  // 移除查询参数和锚点
  const cleanPath = path.split('?')[0].split('#')[0];
  
  // 匹配不同的访问类型
  if (cleanPath.includes('/chat') || cleanPath.includes('/c/')) {
    return 'chat';
  } else if (cleanPath.includes('/workspace')) {
    return 'workspace';
  } else if (cleanPath.includes('/admin')) {
    return 'admin';
  } else if (cleanPath.includes('/settings')) {
    return 'settings';
  } else if (cleanPath.includes('/models')) {
    return 'models';
  } else if (cleanPath.includes('/knowledge')) {
    return 'knowledge';
  } else if (cleanPath.includes('/tools')) {
    return 'tools';
  } else if (cleanPath.includes('/files')) {
    return 'files';
  } else if (cleanPath.includes('/users')) {
    return 'users';
  } else if (cleanPath.includes('/prompts')) {
    return 'prompts';
  } else if (cleanPath.includes('/home') || cleanPath === '/') {
    return 'home';
  } else {
    return 'browse';
  }
};

/**
 * 智能记录页面访问
 * 根据用户登录状态自动选择记录方式
 */
export const trackPageView = async (
  url: string,
  accessType?: string
): Promise<void> => {
  try {
    const token = localStorage.getItem('token');
    const data: PageViewCreateForm = {
      url,
      access_type: accessType || inferAccessType(url)
    };

    if (token) {
      // 用户已登录，记录到用户账户
      await recordPageView(token, data);
    } 
  } catch (error) {
    console.warn('记录页面访问失败:', error);
    // 不要因为统计失败而影响用户体验
  }
};

/**
 * 跟踪当前页面
 */
export const trackCurrentPage = async (accessType?: string): Promise<void> => {
  if (typeof window !== 'undefined') {
    await trackPageView(window.location.pathname, accessType);
  }
};

/**
 * 智能跟踪当前页面（自动推断访问类型）
 */
export const trackCurrentPageSmart = async (): Promise<void> => {
  if (typeof window !== 'undefined') {
    const accessType = inferAccessType(window.location.pathname);
    await trackPageView(window.location.pathname, accessType);
  }
};

/**
 * 防抖函数，避免频繁触发
 */
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as T;
};

/**
 * 防抖版本的页面跟踪
 */
export const trackPageViewDebounced = debounce(trackPageView, 1000);

/**
 * 自动页面跟踪器
 * 监听路由变化并自动记录页面访问
 */
export class PageViewTracker {
  private static instance: PageViewTracker;
  private isTracking = false;
  private lastUrl = '';

  private constructor() {}

  static getInstance(): PageViewTracker {
    if (!PageViewTracker.instance) {
      PageViewTracker.instance = new PageViewTracker();
    }
    return PageViewTracker.instance;
  }

  /**
   * 开始自动跟踪
   */
  startTracking(): void {
    if (this.isTracking || typeof window === 'undefined') return;

    this.isTracking = true;
    this.lastUrl = window.location.pathname;

    // 记录初始页面
    trackCurrentPageSmart();

    // 监听路由变化
    const trackRouteChange = () => {
      const currentUrl = window.location.pathname;
      if (currentUrl !== this.lastUrl) {
        this.lastUrl = currentUrl;
        trackCurrentPageSmart();
      }
    };

    // 监听 popstate 事件（浏览器前进/后退）
    window.addEventListener('popstate', trackRouteChange);

    // 对于 SPA 应用，还需要监听 pushState 和 replaceState
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      setTimeout(trackRouteChange, 0);
    };

    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      setTimeout(trackRouteChange, 0);
    };

    console.log('页面访问跟踪已启动');
  }

  /**
   * 停止自动跟踪
   */
  stopTracking(): void {
    this.isTracking = false;
    console.log('页面访问跟踪已停止');
  }

  /**
   * 获取跟踪状态
   */
  getTrackingStatus(): boolean {
    return this.isTracking;
  }
} 