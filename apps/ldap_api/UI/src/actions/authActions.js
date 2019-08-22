import * as types from './main';
import config from '../config';
import { push } from 'connected-react-router'

export const userActions = {
    login,
    logout,
};

function login(user) {
  return function(dispatch) {
    dispatch({ 
      type: types.LOGIN_USER,
      user 
    });
    fetch(config.api_address + '/login', {
      credentials: "include",
      method: 'POST',
      body: JSON.stringify(user),
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then((response) => {
      if(response.status == 200){

        response.json().then(data => {
          localStorage.setItem('currentUserRole', data.role);
          dispatch({ 
            type: types.LOGIN_USER_SUCCESS,
            user 
          });
          dispatch(push('/'));
        });
      }else{
        alert('No se ha podido autenticar su cuenta. Por favor inténtelo de nuevo.');
        dispatch({ 
          type: types.LOGIN_USER_ERROR,
          user 
        });
      }
    }).catch(err => {
      console.error(err);
      alert('No se ha podido autenticar su cuenta. Por favor inténtelo de nuevo.');
      dispatch({ 
        type: types.LOGIN_USER_ERROR,
        user 
      });
    });
  };
}

function logout() {
  return function(dispatch){
    dispatch({ 
      type: types.LOGOUT_USER
    });
    fetch(config.api_address + '/logout', {
      credentials: "include",
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(res => {
      if (res.status === 200) {
        localStorage.removeItem('currentUserRole');
        dispatch(push('/entrar'));
      } else {
        const error = new Error(res.error);
        throw error;
      }
    })
    .catch(err => {
      console.error(err);
      alert('No se ha podido cerrar la sesión. Por favor inténtelo de nuevo.');
    });
  }
}