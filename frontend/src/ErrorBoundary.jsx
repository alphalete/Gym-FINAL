import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props){ super(props); this.state = { hasError:false, error:null, info:null }; }
  static getDerivedStateFromError(error){ return { hasError:true, error }; }
  componentDidCatch(error, info){ this.setState({ info }); console.error("[ErrorBoundary]", error, info); }
  render(){
    if(!this.state.hasError) return this.props.children;
    return (
      <div style={{padding:16,fontFamily:"system-ui, -apple-system, Segoe UI, Roboto"}}>
        <h2 style={{margin:"8px 0"}}>Something went wrong.</h2>
        <pre style={{whiteSpace:"pre-wrap", background:"#f9fafb", padding:12, borderRadius:8, border:"1px solid #e5e7eb"}}>
{String(this.state.error?.message || this.state.error || "Unknown error")}
        </pre>
        {this.state.info?.componentStack && (
          <details style={{marginTop:8}}>
            <summary>stack</summary>
            <pre style={{whiteSpace:"pre-wrap"}}>{this.state.info.componentStack}</pre>
          </details>
        )}
      </div>
    );
  }
}