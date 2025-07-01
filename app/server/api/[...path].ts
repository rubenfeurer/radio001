// API proxy to forward requests to FastAPI backend
// This allows the Nuxt frontend to communicate with the FastAPI backend seamlessly

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  // Get the path after /api/
  const path = getRouterParam(event, 'path') || ''
  const method = getMethod(event)
  const query = getQuery(event)

  // Backend URL configuration
  const backendHost = process.env.API_HOST || 'localhost'
  const backendPort = process.env.API_PORT || '8000'
  const backendUrl = `http://${backendHost}:${backendPort}`

  // Construct the full backend URL
  const targetUrl = new URL(path, backendUrl)

  // Add query parameters
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined) {
      targetUrl.searchParams.append(key, String(value))
    }
  })

  try {
    // Prepare request options
    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        // Forward relevant headers
        ...(getHeader(event, 'authorization') && {
          'Authorization': getHeader(event, 'authorization')
        }),
      },
    }

    // Handle request body for POST/PUT requests
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      const body = await readBody(event)
      if (body) {
        requestOptions.body = JSON.stringify(body)
      }
    }

    // Make request to FastAPI backend
    const response = await fetch(targetUrl.toString(), requestOptions)

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type')
    let data

    if (contentType?.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    // Set response status
    setResponseStatus(event, response.status)

    // Forward response headers
    response.headers.forEach((value, key) => {
      if (!['content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
        setResponseHeader(event, key, value)
      }
    })

    return data

  } catch (error) {
    console.error('Backend proxy error:', error)

    // Return a structured error response
    setResponseStatus(event, 503)
    return {
      success: false,
      message: 'Backend service unavailable',
      error: process.env.NODE_ENV === 'development' ? error.message : 'Service unavailable'
    }
  }
})
