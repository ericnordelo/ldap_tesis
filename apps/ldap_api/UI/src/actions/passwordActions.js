import * as types from './main';
import config from '../config';
import { push } from 'connected-react-router'

export const passwordActions = {
    change,
    recover,
    recoverPassword,
    start_loading,
    end_loading,
};

function change(data) {
  return function(dispatch) {
    dispatch({ 
        type: types.START_LOADING
    });
    fetch(config.api_address + '/p/cambiar', {
        credentials: "include",
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (res.status === 200) {
            dispatch(push('/entrar'));
            alert('Contraseña cambiada correctamente.');
        } else{
            alert('Sus credenciales son incorrectas.');
        }
        dispatch({ 
            type: types.END_LOADING
        });
    })
    .catch(err => {
        dispatch({ 
            type: types.END_LOADING
        });
        console.error(err);
        alert('Sus credenciales son incorrectas.');
    });
  };
}

function recoverPassword(data) {
  return function(dispatch) {
    dispatch({ 
        type: types.START_LOADING
    });
    fetch(config.api_address + '/p/preguntasdeseguridad', {
        credentials: "include",
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        dispatch(push('/entrar'));
        alert('Su contraseña ha sido actualizada satisfactoriamente.');
        dispatch({ 
            type: types.END_LOADING
        });
    })
    .catch(err => {
        console.error(err);
        alert('Las respuestas no son las adecuadas.');
        dispatch({ 
          type: types.END_LOADING
      });
    });
  };
}

function start_loading(){
    return function(dispatch) {
        dispatch({ 
            type: types.START_LOADING
        });
    };
}

function end_loading(){
    return function(dispatch) {
        dispatch({ 
            type: types.END_LOADING
        });
    };
}

function recover() {
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