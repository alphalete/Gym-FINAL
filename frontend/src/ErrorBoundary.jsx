import React from "react";
import DebugOverlay from "./DebugOverlay";

export default class ErrorBoundary extends React.Component {
  state = { err: null, info: null };
  static getDerivedStateFromError(err){ return { err }; }
  componentDidCatch(err, info){ this.setState({ info }); console.error("[ErrorBoundary]", err, info); }
  render(){
    return (
      <>
        <DebugOverlay error={this.state.err} info={this.state.info} />
        {this.state.err ? null : this.props.children}
      </>
    );
  }
}