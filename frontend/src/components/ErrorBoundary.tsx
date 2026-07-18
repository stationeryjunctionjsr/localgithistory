'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { trackError } from '@/utils/analytics';

interface Props {
  children: ReactNode;
  /**
   * Optional custom fallback UI. Receives `reset` (component-level recovery,
   * no page reload) and `reload` (full page reload) callbacks.
   */
  fallback?: (opts: { error: Error; reset: () => void; reload: () => void }) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false, error: null };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    trackError({
      message: `React Error Boundary: ${error.message}`,
      stack: error.stack + '\nComponent Stack: ' + errorInfo.componentStack,
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = () => {
    if (typeof window !== 'undefined') window.location.reload();
  };

  public render() {
    if (!this.state.hasError) return this.props.children;

    if (this.props.fallback) {
      return this.props.fallback({
        error: this.state.error!,
        reset: this.handleReset,
        reload: this.handleReload,
      });
    }

    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 px-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
          <svg
            className="h-7 w-7 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.8}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Something went wrong</h2>
          <p className="mt-1 text-sm text-gray-500">
            Our team has been notified. You can try again or refresh the page.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={this.handleReset}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 active:bg-gray-100"
          >
            Try again
          </button>
          <button
            onClick={this.handleReload}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 active:bg-blue-800"
          >
            Refresh page
          </button>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
