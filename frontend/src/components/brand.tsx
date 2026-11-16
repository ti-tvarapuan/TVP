import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/components/theme-provider"

export function Brand() {
  return <a className="brand" href="#inicio" aria-label="TVP, início"><span className="brand-mark">TVP</span></a>
}

export function SiteHeader() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === "dark"

  return <header className="site-header">
    <a className="header-link" href="#sobre">Sobre mim</a>
    <div className="header-actions">
      <button className="theme-toggle" type="button" onClick={() => setTheme(isDark ? "light" : "dark")} aria-label={`Ativar tema ${isDark ? "claro" : "escuro"}`} title={`Tema ${isDark ? "claro" : "escuro"}`}>
        {isDark ? <Sun size={17} /> : <Moon size={17} />}
      </button>
      <Brand />
    </div>
  </header>
}
