export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
  errors?: Record<string, string[]>;
}

export function handleApiError(error: any): string {
  // Axios error with response
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;

    // Handle specific error structures
    if (data?.detail) {
      return data.detail;
    }

    if (data?.message) {
      return data.message;
    }

    // Handle validation errors (422)
    if (status === 422 && data?.errors) {
      const errorMessages = Object.entries(data.errors)
        .map(([field, messages]) => `${field}: ${(messages as string[]).join(', ')}`)
        .join('; ');
      return errorMessages || 'Validation failed';
    }

    // Handle common HTTP status codes
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'You are not authorized. Please login again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'This item already exists or conflicts with existing data.';
      case 422:
        return 'The submitted data is invalid. Please check your input.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return data?.message || 'An unexpected error occurred';
    }
  }

  // Axios error without response (network error)
  if (error.request) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please check your connection and try again.';
    }
    return 'Unable to connect to server. Please check your internet connection.';
  }

  // Handle error object with message
  if (error.message) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  // Fallback
  return 'An unexpected error occurred. Please try again.';
}

export function getErrorStatus(error: any): number | undefined {
  return error.response?.status;
}

export function isAuthError(error: any): boolean {
  const status = getErrorStatus(error);
  return status === 401 || status === 403;
}

export function isValidationError(error: any): boolean {
  return getErrorStatus(error) === 422;
}

export function isNetworkError(error: any): boolean {
  return !!error.request && !error.response;
}

export function getValidationErrors(error: any): Record<string, string[]> | null {
  if (isValidationError(error)) {
    return error.response?.data?.errors || null;
  }
  return null;
}
