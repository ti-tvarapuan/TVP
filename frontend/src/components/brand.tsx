import { ArrowRight } from "lucide-react"

export function Brand() {
  return <a className="brand" href="#inicio" aria-label="TVP, início"><span className="brand-mark">TVP</span><span className="brand-name">transcritor<span> de vídeo</span></span></a>
}

export function SiteHeader() {
  return <header className="site-header"><Brand /><div className="header-note"><span className="status-indicator" /> Tradução simples, do inglês ao português</div><a className="header-link" href="#como-funciona">Como funciona <ArrowRight size={14} /></a></header>
}
