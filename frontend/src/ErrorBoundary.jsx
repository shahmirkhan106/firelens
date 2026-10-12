import React from "react";

/**
 * Catches render errors in a chart so one bad payload shows a message instead of
 * unmounting the whole app (a blank page that "needs a refresh").
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(prev) {
    if (this.state.error && prev.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="load err">
          <p>This view could not be displayed.</p>
          <p style={{ fontSize: 11, opacity: 0.7 }}>{String(this.state.error.message || this.state.error)}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
