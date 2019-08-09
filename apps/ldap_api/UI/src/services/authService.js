import config from '../config'

export const loginUserService = (request) => {
  return fetch(config.api_address + '/login', {
    credentials: "include",
    method: 'POST',
    body: JSON.stringify(request.user),
    headers: {
      'Content-Type': 'application/json'
    }
    })
    .then(response => {
      return response.json();
    })
    .then(json => {
      return json;
    });
};

export const logout = () => {
  // remove user from local storage to log user out
  // localStorage.removeItem('user');
}

export const handleResponse = (response) => response.text().then(text => {
    const data = text && JSON.parse(text);
    if (!response.ok) {
        if (response.status === 401) {
            // auto logout if 401 response returned from api
            logout();
        }

        const error = (data && data.message) || response.statusText;
        return Promise.reject(error);
    }

    return data;
});
