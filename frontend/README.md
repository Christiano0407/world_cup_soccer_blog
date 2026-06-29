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

## Análisis del Proyecto — 6 Procesos

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                  world_cup_soccer_blog                   │
                    │           Monorepo — pnpm workspace                     │
                    └─────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────┬──────────┼──────────┬─────────────────┬──────────┐
        ▼                 ▼          ▼          ▼                 ▼          ▼
  ① DB             ② Storage    ③ Workers  ④ Backend   ⑤ Gateway     ⑥ Frontend
  PostgreSQL       MinIO        ETL (CSV)  FastAPI      Nginx          React + TS
  Port 5434        Ports        Python     Port 8000    Port 8080      Port 5173
  (host:5432)      9000/9001    uv run     JWT Auth     Proxy API      CSR + TanStack
                                                      SPA fallback
```

| Proceso | Tecnología | Rol en el sistema | Conexión con Frontend |
|---------|-----------|-------------------|----------------------|
| **① DB** | PostgreSQL 15 | Almacena datos históricos de mundiales (equipos, partidos, torneos, jugadores, usuarios) | El frontend nunca accede directo; todo viaja por la API |
| **② Storage** | MinIO | Almacena CSVs, imágenes, datos procesados por workers | No hay acceso directo desde frontend |
| **③ Workers** | Python (uv) | ETL: ingesta de CSVs → PostgreSQL + MinIO | No interactúa con frontend |
| **④ Backend** | FastAPI (Python) | API REST con JWT auth, rate limiting (60 req/min), Prometheus, OpenAPI docs | **Endpoint principal del frontend** — todas las llamadas van aquí |
| **⑤ Gateway** | Nginx | Reverse proxy: rutas `/api/*` → backend, `/` → frontend SPA | Punto de entrada único en producción (`:8080`) |
| **⑥ Frontend** | React 19 + Vite 8 | CSR — TanStack Query consulta la API y renderiza datos | **Este proyecto** |

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

## Pipeline Maestro — Conexión Frontend → Backend (6 Fases)

Diagrama de flujo de datos extremo a extremo:

```
          React Component
               │
               ▼
    useQuery(['teams'], fetchTeams)
               │
        ┌──────┴──────┐
        ▼              ▼
   {isLoading}     {data, error}
        │              │
        ▼              ▼
   <Loading />    <TeamList teams={data} />
                        │
                        ▼
          fetch('/api/v1/teams/')
                        │
               ┌────────┴────────┐
               ▼                  ▼
         Dev (5173)           Prod (8080)
         Vite Proxy           Nginx Proxy
               │                  │
               └──────┬───────────┘
                      ▼
              backend:8000
              (FastAPI)
                      │
                      ▼
              Service Layer
                      │
                      ▼
              SQLAlchemy ORM
                      │
                      ▼
              PostgreSQL
```

---

### Fase 0 — Catálogo de Endpoints (Backend)

Todos los endpoints públicos que el frontend puede consumir. Sin autenticación para lectura de datos históricos.

| Endpoint | Método | Auth | Params | Respuesta |
|----------|--------|------|--------|-----------|
| `GET /api/v1/teams/` | GET | — | `active`, `confederation` | `Team[]` |
| `GET /api/v1/teams/ranking` | GET | — | — | `Team[]` |
| `GET /api/v1/teams/{initials}` | GET | — | — | `Team + TeamStats` |
| `GET /api/v1/teams/{initials}/matches` | GET | — | `page`, `page_size`, `stage`, `year` | `Paginated<Match>` |
| `GET /api/v1/teams/{initials}/head-to-head/{opponent}` | GET | — | — | `HeadToHead` |
| `GET /api/v1/matches/` | GET | — | `page`, `page_size`, `team`, `year`, `stage` | `Paginated<Match>` |
| `GET /api/v1/matches/{id}` | GET | — | — | `Match` |
| `GET /api/v1/matches/{id}/players` | GET | — | — | `PlayerAppearance[]` |
| `GET /api/v1/tournaments/` | GET | — | `page`, `page_size` | `Paginated<Tournament>` |
| `GET /api/v1/tournaments/{year}` | GET | — | — | `Tournament` |
| `GET /api/v1/tournaments/{year}/matches` | GET | — | `page`, `page_size` | `Paginated<Match>` |
| `GET /api/v1/tournaments/{year}/teams` | GET | — | — | `Team[]` |
| `GET /api/v1/tournaments/{year}/top-scorers` | GET | — | — | `TopScorer[]` |
| `GET /api/v1/players/search` | GET | — | `q` | `PlayerAppearance[]` |
| `GET /api/v1/players/top-scorers` | GET | — | — | `TopScorer[]` |
| `GET /api/v1/players/{name}/career` | GET | — | — | `PlayerCareer` |
| `POST /api/v1/auth/register` | POST | — | `RegisterIn` body | `TokenOut` |
| `POST /api/v1/auth/login` | POST | — | `LoginIn` body | `TokenOut` |
| `POST /api/v1/auth/refresh` | POST | Cookie | — | `TokenOut` |
| `POST /api/v1/auth/logout` | POST | Bearer | — | `void` |
| `GET /api/v1/auth/me` | GET | Bearer | — | `UserOut` |
| `PATCH /api/v1/auth/me` | PATCH | Bearer | `UserUpdateIn` body | `UserOut` |
| `POST /api/v1/auth/change-password` | POST | Bearer | `ChangePasswordIn` body | `void` |

---

### Fase 1 — Tipos TypeScript (`src/api/types.ts`)

Mapear cada schema de OpenAPI a una interfaz TypeScript. Esto es el **contrato** entre frontend y backend.

```typescript
// = Equipos = //
export interface Team {
  team_id: number
  initials: string
  name: string
  confederation: string
  fifa_code: string
  active: boolean
}

export interface TeamStats {
  tournaments_played: number
  titles: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  win_rate: number
  points: number
}

export interface HeadToHead {
  team1_initials: string
  team2_initials: string
  team1_wins: number
  team2_wins: number
  draws: number
  total_matches: number
}

// = Partidos = //
export interface Match {
  match_id: number
  tournament_year: number
  stage: string
  date: string
  team1_initials: string
  team2_initials: string
  team1_name: string
  team2_name: string
  team1_goals: number
  team2_goals: number
  team1_penalties?: number
  team2_penalties?: number
  stadium: string
  city: string
  referee: string
  attendance?: number
}

// = Torneos = //
export interface Tournament {
  year: number
  host_country: string
  winner: string
  runners_up: string
  third_place: string
  fourth_place: string
  goals_scored: number
  matches_played: number
  attendance: number
  start_date: string
  end_date: string
}

// = Jugadores = //
export interface PlayerAppearance {
  player_match_id: number
  match_id: number
  team_initials: string
  player_name: string
  position: string
  event_code: string | null
  shirt_number: number
}

export interface TopScorer {
  player_name: string
  goals: number
  own_goals: number
  matches_played: number
  editions: number[]
}

export interface PlayerCareer {
  player_name: string
  appearances: number
  starts: number
  substitutions: number
  goals: number
  yellow_cards: number
  red_cards: number
  editions: number[]
}

// = Genéricos = //
export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// = Autenticación = //
export interface LoginIn {
  email: string
  password: string
}

export interface RegisterIn {
  email: string
  password: string
  display_name: string
}

export interface TokenOut {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserOut {
  user_id: number
  email: string
  display_name: string
  role: 'admin' | 'editor' | 'reader'
  is_active: boolean
  created_at: string
  updated_at: string
}
```

---

### Fase 2 — Fetch Wrapper Nativo (`src/api/client.ts`)

Cada llamada al backend usa `fetch()` nativo. Sin axios, sin ky. La URL relativa (`/api/v1/...`) funciona tanto en desarrollo (Vite proxy) como en producción (Nginx).

```
┌──────────────────────────────────────────────────────────────┐
│                        Navegador                              │
│                                                               │
│  src/api/client.ts                                            │
│  ┌─────────────────────────────────────┐                     │
│  │ client.listTeams()                  │                     │
│  │   → fetch('/api/v1/teams/')         │  Dev: Vite proxy    │
│  │   → fetch('http://localhost:5173/   │  ─────────────────── │
│  │              api/v1/teams/')        │  → backend:8000     │
│  │                                     │                     │
│  │                                     │  Prod: Nginx        │
│  │                                     │  ─────────────────── │
│  │                                     │  → backend:8000     │
│  └─────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

Contrato del wrapper:

| Operación | Firma | Endpoint |
|-----------|-------|----------|
| Listar equipos | `listTeams(params?)` | `GET /api/v1/teams/` |
| Detalle equipo | `getTeam(initials)` | `GET /api/v1/teams/{initials}` |
| Partidos equipo | `getTeamMatches(initials, params?)` | `GET /api/v1/teams/{initials}/matches` |
| Head-to-head | `getHeadToHead(t1, t2)` | `GET /api/v1/teams/{t1}/head-to-head/{t2}` |
| Ranking | `getRanking()` | `GET /api/v1/teams/ranking` |
| Listar partidos | `listMatches(params?)` | `GET /api/v1/matches/` |
| Detalle partido | `getMatch(id)` | `GET /api/v1/matches/{id}` |
| Alineación | `getMatchPlayers(id)` | `GET /api/v1/matches/{id}/players` |
| Listar torneos | `listTournaments(params?)` | `GET /api/v1/tournaments/` |
| Detalle torneo | `getTournament(year)` | `GET /api/v1/tournaments/{year}` |
| Partidos torneo | `getTournamentMatches(year, params?)` | `GET /api/v1/tournaments/{year}/matches` |
| Equipos torneo | `getTournamentTeams(year)` | `GET /api/v1/tournaments/{year}/teams` |
| Goleadores torneo | `getTournamentTopScorers(year)` | `GET /api/v1/tournaments/{year}/top-scorers` |
| Buscar jugadores | `searchPlayers(q)` | `GET /api/v1/players/search` |
| Goleadores históricos | `getTopScorers()` | `GET /api/v1/players/top-scorers` |
| Carrera jugador | `getPlayerCareer(name)` | `GET /api/v1/players/{name}/career` |
| Login | `login(data)` | `POST /api/v1/auth/login` |
| Registro | `register(data)` | `POST /api/v1/auth/register` |
| Logout | `logout()` | `POST /api/v1/auth/logout` |
| Perfil | `getMe()` | `GET /api/v1/auth/me` |

Comportamiento interno del wrapper:

1. **URL relativa**: todas las rutas empiezan con `/api/v1/...`
2. **Token JWT**: se lee de `localStorage` y se inyecta como `Authorization: Bearer <token>`
3. **Error 401**: si el backend rechaza el token, se limpia `localStorage`
4. **Parseo JSON**: cada respuesta se tipa con las interfaces de `types.ts`

---

### Fase 3 — TanStack Query Hooks (`src/hooks/`)

Cada hook envuelve una llamada del `client` y expone `data`, `isLoading`, `error`.

```
Componente React
     │
     ▼
useTeams()  ← TanStack Query useQuery
     │
     ▼
client.listTeams()  ← fetch wrapper
     │
     ▼
fetch('/api/v1/teams/')
     │
     ▼
Proxy Vite (dev) / Nginx (prod)
     │
     ▼
backend:8000 (FastAPI → PostgreSQL)
```

Catálogo de hooks:

| Hook | Tipo | Query Key | Endpoint que consume |
|------|------|-----------|---------------------|
| `useTeams(params?)` | `useQuery` | `['teams', params]` | `GET /api/v1/teams/` |
| `useTeam(initials)` | `useQuery` | `['team', initials]` | `GET /api/v1/teams/{initials}` |
| `useTeamMatches(initials, page?)` | `useQuery` | `['teamMatches', initials, page]` | `GET /api/v1/teams/{initials}/matches` |
| `useHeadToHead(t1, t2)` | `useQuery` | `['headToHead', t1, t2]` | `GET /api/v1/teams/{t1}/head-to-head/{t2}` |
| `useRanking()` | `useQuery` | `['ranking']` | `GET /api/v1/teams/ranking` |
| `useMatches(params?)` | `useQuery` | `['matches', params]` | `GET /api/v1/matches/` |
| `useMatch(id)` | `useQuery` | `['match', id]` | `GET /api/v1/matches/{id}` |
| `useMatchPlayers(id)` | `useQuery` | `['matchPlayers', id]` | `GET /api/v1/matches/{id}/players` |
| `useTournaments(page?)` | `useQuery` | `['tournaments', page]` | `GET /api/v1/tournaments/` |
| `useTournament(year)` | `useQuery` | `['tournament', year]` | `GET /api/v1/tournaments/{year}` |
| `useTournamentMatches(year, page?)` | `useQuery` | `['tournamentMatches', year, page]` | `GET /api/v1/tournaments/{year}/matches` |
| `useTournamentTeams(year)` | `useQuery` | `['tournamentTeams', year]` | `GET /api/v1/tournaments/{year}/teams` |
| `useTournamentTopScorers(year)` | `useQuery` | `['tournamentTopScorers', year]` | `GET /api/v1/tournaments/{year}/top-scorers` |
| `useMe()` | `useQuery` | `['me']` | `GET /api/v1/auth/me` |
| `useLogin()` | `useMutation` | — | `POST /api/v1/auth/login` |
| `useRegister()` | `useMutation` | — | `POST /api/v1/auth/register` |
| `useLogout()` | `useMutation` | — | `POST /api/v1/auth/logout` |

**Regla de arquitectura**: Ninguna Page importa `client.ts` directamente. Siempre a través de hooks. Esto permite cambiar la implementación HTTP (fetch → ky → axios) sin tocar la UI.

---

### Fase 4 — Autenticación (Auth Flow)

```
┌─────────┐     POST /api/v1/auth/login      ┌──────────────┐
│ Login   │ ────────────────────────────────→ │  Backend     │
│ Page    │                                   │  FastAPI     │
│         │ ←──────────────────────────────── │              │
└─────────┘     { access_token, expires_in }  └──────────────┘
                      │
                      ▼
               localStorage.setItem('token', access_token)
                      │
                      ▼
               TanStack Query cache se invalida
                      │
                      ▼
               useMe() se ejecuta automáticamente
                      │
                      ▼
               Navbar muestra "Logged in as: user"
```

**Flujo de request autenticado**:

```
fetch('/api/v1/auth/me', {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`
  }
})
  │
  ├── ✅ 200 → data (UserOut)
  │
  └── ❌ 401 → localStorage.removeItem('token')
               → useMe() se desactiva (enabled: !!token)
               → Navbar muestra botón "Login"
```

---

### Fase 5 — Mapa de Dependencias entre Capas

```
src/api/types.ts         ← Contrato: define formas de datos (interfaces TS)
     ↑                          Basado en los schemas de backend/openapi/
     │
src/api/client.ts        ← Fetch wrapper: llama a endpoints, parsea JSON, tipa respuestas
     ↑                          Inyecta token JWT automáticamente
     │
src/hooks/use*.ts        ← TanStack Query: caching automático, estados loading/error/success
     ↑                          Cada hook = un queryKey + un queryFn del client
     │
src/pages/*.tsx          ← UI: consume hooks con useQuery/useMutation, renderiza con Tailwind
     ↑                          Decide qué mostrar según isLoading / data / error
     │
src/components/*.tsx     ← Componentes reutilizables: Card, ScoreDisplay, Badge, Loading
                                  Sin lógica de datos, solo reciben props
```

**Flujo de ejemplo — HomePage mostrando equipos**:

```
1. Home.tsx                    →  useTeams({ active: true })
2. useTeams.ts                 →  client.listTeams({ active: true })
3. client.ts                   →  fetch('/api/v1/teams/?active=true')
4. Vite proxy (dev)            →  http://backend:8000/api/v1/teams/?active=true
5. backend (FastAPI)           →  SELECT * FROM teams WHERE active = true
6. PostgreSQL                  →  [ { team_id: 1, initials: 'BRA', ... }, ... ]
7. ← JSON response             →  fetch wrapper parsea y tipa como Team[]
8. ← TanStack cachea           →  useTeams devuelve { data, isLoading, error }
9. Home.tsx renderiza          →  {isLoading ? <Loading/> : <TeamGrid data={data}/>}
```

---

### Fase 6 — Comandos de Conexión y Verificación

```bash
# ========================================
# ENTORNO DE DESARROLLO
# ========================================

# 1. Iniciar infraestructura (DB + backend)
docker compose up -d postgres redis backend

# 2. Verificar que el backend responde
curl http://localhost:8000/api/v1/teams/ | jq '.items[:2]'

# 3. Iniciar frontend en modo dev
cd frontend && pnpm dev

# 4. Probar conexión vía Vite proxy
curl http://localhost:5173/api/v1/teams/ | jq '.items[:2]'
# → Vite proxy → backend:8000 → PostgreSQL → JSON

# ========================================
# ENTORNO DE PRODUCCIÓN (Docker Compose)
# ========================================

# 5. Construir y levantar todo
docker compose build frontend
docker compose up -d

# 6. Verificar conexión vía Nginx gateway
curl http://localhost:8080/api/v1/teams/ | jq '.items[:2]'
# → Nginx → backend:8000 → PostgreSQL → JSON

# 7. Verificar SPA
curl -s http://localhost:8080/ | head -5
# → <!DOCTYPE html>... (index.html servido por frontend)
```

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

El proxy de Vite redirige `/api/*` → `backend:8000` (ver `vite.config.ts`). En producción, Nginx redirige la misma ruta.

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `GET /api/v1/teams/` | GET | — | Lista de selecciones (filtro: `active`, `confederation`) |
| `GET /api/v1/teams/ranking` | GET | — | Ranking histórico |
| `GET /api/v1/teams/{initials}` | GET | — | Detalle + estadísticas de una selección |
| `GET /api/v1/teams/{initials}/matches` | GET | — | Historial de partidos (paginado) |
| `GET /api/v1/teams/{initials}/head-to-head/{opponent}` | GET | — | Head-to-head entre dos equipos |
| `GET /api/v1/matches/` | GET | — | Lista de partidos (paginado, filtro: `team`, `year`, `stage`) |
| `GET /api/v1/matches/{id}` | GET | — | Detalle de partido |
| `GET /api/v1/matches/{id}/players` | GET | — | Alineaciones del partido |
| `GET /api/v1/tournaments/` | GET | — | Lista de mundiales (paginado) |
| `GET /api/v1/tournaments/{year}` | GET | — | Detalle de edición |
| `GET /api/v1/tournaments/{year}/matches` | GET | — | Partidos de una edición |
| `GET /api/v1/tournaments/{year}/teams` | GET | — | Equipos participantes |
| `GET /api/v1/tournaments/{year}/top-scorers` | GET | — | Goleadores de la edición |
| `GET /api/v1/players/search` | GET | — | Buscar jugadores por nombre |
| `GET /api/v1/players/top-scorers` | GET | — | Goleadores históricos |
| `GET /api/v1/players/{name}/career` | GET | — | Carrera completa de un jugador |
| `POST /api/v1/auth/register` | POST | — | Registro de usuario |
| `POST /api/v1/auth/login` | POST | — | Inicio de sesión |
| `POST /api/v1/auth/refresh` | POST | Cookie | Refrescar token |
| `POST /api/v1/auth/logout` | POST | Bearer | Cerrar sesión |
| `GET /api/v1/auth/me` | GET | Bearer | Perfil del usuario autenticado |
| `PATCH /api/v1/auth/me` | PATCH | Bearer | Actualizar perfil |
| `POST /api/v1/auth/change-password` | POST | Bearer | Cambiar contraseña |

---

## Historial de cambios

| Fecha | Cambio |
|-------|--------|
| 2026-06-29 | Se agregó análisis de 6 procesos del proyecto, pipeline de conexión frontend→backend (Fases 0–6), catálogo completo de endpoints, tipos TypeScript, fetch wrapper, hooks TanStack Query, auth flow, mapa de dependencias y comandos de verificación. |
| 2026-06-25 | Se eliminó `axios` por seguridad (supply chain attack). Se migró a **fetch nativo**. |

---

## Notas

- **Ancho del build**: ~257 KB JS + ~7 KB CSS (gzip: ~82 KB total)
- **Tailwind v4** no necesita `tailwind.config.ts` ni `postcss.config.js`. Usa `@import "tailwindcss"` en CSS y el plugin `@tailwindcss/vite` en Vite.
- **TypeScript 6.0.3** instalado. Usar `tsc --noEmit` para type-check.
- **Fetch nativo** reemplazó a axios (abril 2025 — supply chain attack). Sin dependencias HTTP externas. Fácil migrar a `ky` después si se necesita timeout/retry.
- El `Dockerfile` y `docker-compose.yml` están en skeleton — completar antes de deploy.
- Para migrar a `ky` después: `pnpm add ky` y cambiar solo `api/client.ts`.
