import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

const STORAGE_KEY = 'carleon.apiKey'

interface ApiKeyState {
  apiKey: string
  setApiKey: (key: string) => void
}

const ApiKeyContext = createContext<ApiKeyState | null>(null)

function readStored(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

/**
 * Пока нет авторизации (auth-эндпоинтов в бэкенде ещё нет), операции записи
 * защищены общим X-API-Key. Ключ вводится вручную и хранится в браузере.
 */
export function ApiKeyProvider({ children }: { children: ReactNode }) {
  const [apiKey, setKey] = useState(readStored)

  const setApiKey = useCallback((key: string) => {
    setKey(key)
    try {
      if (key) localStorage.setItem(STORAGE_KEY, key)
      else localStorage.removeItem(STORAGE_KEY)
    } catch {
      /* localStorage недоступен — ключ живёт только до перезагрузки */
    }
  }, [])

  const value = useMemo(() => ({ apiKey, setApiKey }), [apiKey, setApiKey])
  return <ApiKeyContext.Provider value={value}>{children}</ApiKeyContext.Provider>
}

export function useApiKey(): ApiKeyState {
  const ctx = useContext(ApiKeyContext)
  if (!ctx) throw new Error('useApiKey должен использоваться внутри ApiKeyProvider')
  return ctx
}
