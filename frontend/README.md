# Frontend — World Cup Soccer Blog

CSR + Vite + React 19 + TypeScript + TailwindCSS v4 + TanStack Query

---

## Arquitectura

```
┌──────────────────────────────────────────────────┐
│                   Navegador                       │
│         https://tu-dominio (localhost.run)        │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
          nginx gateway (data_world_nginx)
          puerto 8080 (host) → 80 (container)
           ┌──────────────────────────────┐
           │                              │
  /api/* ──┤                    / ────────┤
           ▼                              ▼
   backend:8000                   frontend:80
   (FastAPI)                      (nginx estático)
                                     │
                                     ▼
                             /usr/share/nginx/html
                             index.html, assets/*.js
                             (SPA fallback → index.html)
```

## Stack

| Capa | Tecnología |
|------|-----------|
| Framework | React 19 + TypeScript |
| Bundler | Vite 8 |
| Estilos | TailwindCSS v4 (vite plugin) |
| Data Fetching | TanStack Query v5 |
| HTTP Client | Fetch nativo |
| Routing | React Router DOM v7 |
| Animaciones | GSAP |
| Linting | ESLint + typescript-eslint |

---

## Pipeline / Mapa Maestro

### Fase 1 — Inicialización del workspace (ya hecho)

```bash
# Raíz del monorepo
pnpm init
pnpm-workspace.yaml  →  packages: ["frontend"]
```

### Fase 2 — Creación del proyecto Vite (ya hecho)

```bash
cd frontend
pnpm create vite . --template react-ts
# Se eliminaron archivos JS, se configuró TypeScript manualmente
```

### Fase 3 — Dependencias instaladas (ya hecho)

```bash
# Producción
pnpm add @tanstack/react-query react-router-dom

# Desarrollo
pnpm add -D tailwindcss @tailwindcss/vite gsap typescript typescript-eslint
```

### Fase 4 — Configuración (ya hecho)

| Archivo | Propósito |
|---------|-----------|
| `vite.config.ts` | Plugin React + Tailwind + Proxy `/api → backend:8000` |
| `tsconfig.json` | Project references |
| `tsconfig.app.json` | TS config para `src/` |
| `tsconfig.node.json` | TS config para `vite.config.ts` |
| `eslint.config.js` | Flat config cubriendo `.ts/.tsx` y `.js/.jsx` |
| `src/index.css` | `@import "tailwindcss"` |
| `src/main.tsx` | `QueryClientProvider` + `createRoot` |
| `src/App.tsx` | `BrowserRouter` + `Routes` placeholder |

### Fase 5 — Infraestructura (ya hecho)

| Archivo | Cambio |
|---------|--------|
| `infra/nginx/conf.d/api-gateway.conf` | `location /` → `proxy_pass http://frontend:80` |
| `docker-compose.yml` | Servicio `frontend` agregado (skeleton) |
| `Dockerfile` | Skeleton listo para llenar |

### Fase 6 — Pendiente: Código de la app

```
frontend/src/
├── api/
│   ├── types.ts        # Interfaces TS (Team, Match, Tournament, etc.)
│   └── client.ts       # fetch wrapper con endpoints
├── hooks/
│   ├── useTeams.ts     # useQuery teams, team detail, ranking
│   ├── useMatches.ts   # useQuery matches, match detail
│   ├── useTournaments.ts # useQuery tournaments, ediciones
│   └── useAuth.ts      # useMutation login/register, useQuery me
├── pages/
│   ├── Home.tsx
│   ├── Teams.tsx
│   ├── TeamDetail.tsx
│   ├── Matches.tsx
│   ├── Tournaments.tsx
│   ├── Login.tsx
│   └── Register.tsx
└── components/
    ├── Layout.tsx
    ├── Navbar.tsx
    ├── Loading.tsx
    └── ...
```

### Fase 7 — Dockerizar (tú llenas)

- `frontend/Dockerfile` — multi-stage build (node → nginx)
- `docker-compose.yml` — servicio `frontend` con networks y depends_on

---

## Comandos

```bash
# Desarrollo
pnpm dev              # Inicia Vite dev server en :5173

# Build
pnpm build            # Producción build → dist/

# Preview
pnpm preview          # Sirve build localmente

# Lint
pnpm lint             # ESLint sobre todo el proyecto

# Typecheck
pnpm tsc              # npx tsc --noEmit (type-check sin emitir)
```

### Docker

```bash
# Build de la imagen
docker build -t frontend ./frontend

# Ejecutar contenedor
docker run -p 3000:80 frontend
```

### Monorepo (desde la raíz)

```bash
# Iniciar solo frontend
pnpm --filter frontend dev

# Build solo frontend
pnpm --filter frontend build
```

---

## API Endpoints (Backend)

El proxy de Vite redirige `/api/*` → `backend:8000` (ver `vite.config.ts`).

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/teams/` | Lista de selecciones |
| `GET /api/v1/teams/{initials}` | Detalle + estadísticas |
| `GET /api/v1/matches/` | Lista de partidos (paginado) |
| `GET /api/v1/matches/{id}` | Detalle de partido |
| `GET /api/v1/tournaments/` | Lista de mundiales |
| `GET /api/v1/tournaments/{year}` | Detalle de edición |
| `POST /api/v1/auth/login` | Login |
| `POST /api/v1/auth/register` | Registro |
| `GET /api/v1/auth/me` | Perfil actual |

---

## Historial de cambios

| Fecha | Cambio |
|-------|--------|
| 2026-06-25 | Se eliminó `axios` por seguridad (supply chain attack). Se migró a **fetch nativo**. |

---

## Notas

- **Ancho del build**: ~257 KB JS + ~7 KB CSS (gzip: ~82 KB total)
- **Tailwind v4** no necesita `tailwind.config.ts` ni `postcss.config.js`. Usa `@import "tailwindcss"` en CSS y el plugin `@tailwindcss/vite` en Vite.
- **TypeScript 6.0.3** instalado. Usar `tsc --noEmit` para type-check.
- **Fetch nativo** reemplazó a axios (abril 2025 — supply chain attack). Sin dependencias HTTP externas. Fácil migrar a `ky` después si se necesita timeout/retry.
- El `Dockerfile` y `docker-compose.yml` están en skeleton — completar antes de deploy.
- Para migrar a `ky` después: `pnpm add ky` y cambiar solo `api/client.ts`.
