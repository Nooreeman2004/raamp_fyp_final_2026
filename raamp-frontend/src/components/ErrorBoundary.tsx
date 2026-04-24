import React, { Component, ErrorInfo, ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

/** Paths that are themselves error-prone and should not be used as fallback navigation targets. */
const UNSAFE_FALLBACK_PATHS = ["/dashboard", "/admin", "/ab-optimizer"];

/**
 * Wrapper that reads the current pathname for ErrorBoundary.
 * Class components cannot call hooks, so we forward the location as a prop.
 */
function ErrorBoundaryWithLocation(props: Props) {
  const location = useLocation();
  return <ErrorBoundaryInner {...props} currentPath={location.pathname} />;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface InnerProps extends Props {
  currentPath: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundaryInner extends Component<InnerProps, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // You can also log to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
          <Card className="w-full max-w-2xl p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-8 h-8 text-destructive" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-destructive">Something went wrong</h1>
                  <p className="text-muted-foreground mt-1">
                    We encountered an unexpected error. Please try again.
                  </p>
                </div>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg border border-primary/10">
                <div className="flex justify-between items-center mb-2">
                  <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
                    Reference ID: {Math.random().toString(36).substring(2, 10).toUpperCase()}
                  </p>
                  <p className="text-[10px] font-mono text-muted-foreground/50">
                    {new Date().toISOString()}
                  </p>
                </div>
                
                {this.state.error && (
                  <details className="mt-2 group">
                    <summary className="text-sm text-primary/70 cursor-pointer hover:text-primary transition-colors flex items-center gap-2 font-mono">
                      <span className="group-open:rotate-90 transition-transform">▶</span>
                      Technical details
                    </summary>
                    <div className="mt-4 space-y-4">
                      <div className="p-3 bg-background rounded border border-destructive/20">
                        <p className="text-sm font-mono text-destructive">
                          {this.state.error.toString()}
                        </p>
                      </div>
                      {this.state.errorInfo && (
                        <pre className="text-[10px] text-muted-foreground overflow-auto max-h-48 p-3 bg-background rounded border border-border/50">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      )}
                    </div>
                  </details>
                )}
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={this.handleReset}
                  variant="default"
                  className="flex-1"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                {/* Prevent infinite redirect: if the error is on /dashboard itself, go home */}
                {(() => {
                  const isSafe = !UNSAFE_FALLBACK_PATHS.some(p =>
                    this.props.currentPath?.startsWith(p)
                  );
                  const fallbackPath = isSafe ? this.props.currentPath ?? "/" : "/";
                  const label = fallbackPath === "/" ? "Go to Home" : "Go to Dashboard";
                  return (
                    <Link to={fallbackPath} className="flex-1">
                      <Button variant="outline" className="w-full">
                        <Home className="w-4 h-4 mr-2" />
                        {label}
                      </Button>
                    </Link>
                  );
                })()}
              </div>

              <div className="text-center text-sm text-muted-foreground">
                <p>
                  If this problem persists, please{" "}
                  <a
                    href="mailto:support@raamp.com"
                    className="text-primary hover:underline"
                  >
                    contact support
                  </a>
                  .
                </p>
              </div>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundaryWithLocation;
