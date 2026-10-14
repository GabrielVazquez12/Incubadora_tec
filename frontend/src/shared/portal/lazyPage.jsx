import { Component, lazy } from 'react';

export const lazyPage = (load, name = 'default') => lazy(() => load().then(module => ({ default: module[name] })));

export class PageBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidUpdate(previous) {
    if (this.state.failed && previous.resetKey !== this.props.resetKey) this.setState({ failed: false });
  }
  render() {
    return this.state.failed ? <section className="panel" role="alert"><h1>No se pudo cargar esta pantalla</h1><p>Comprueba tu conexión y vuelve a intentarlo.</p><button className="button secondary" onClick={() => window.location.reload()}>Reintentar</button></section> : this.props.children;
  }
}
