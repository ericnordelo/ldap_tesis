import * as types from './main';
import config from '../config';
import { push } from 'connected-react-router'

export const userActions = {
    addWorker,
    addStudent,
};

function addWorker(data) {
  return function(dispatch) {
    dispatch({ 
        type: types.START_LOADING
    });
    fetch(config.api_address + '/estudiantes', {
        credentials: "include",
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (res.status === 200) {
            dispatch(push('/p/cambiar'));
            alert('Trabajador agregado satisfactoriamente con el correo: por favor cambie su contraseña.');
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
        alert('Ha ocurrido un error mientras se agregaba la cuenta.');
    });
  };
}

function addStudent(data) {
    return function(dispatch) {
        dispatch({ 
            type: types.START_LOADING
        });
        fetch(config.api_address + '/trabajadores', {
            credentials: "include",
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
              'Content-Type': 'application/json'
            }
        })
        .then(res => {
            if (res.status === 200) {
                dispatch(push('/p/cambiar'));
                alert('Estudiante agregado satisfactoriamente con el correo: por favor cambie su contraseña.');
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
            alert('Ha ocurrido un error mientras se agregaba la cuenta.');
        });
    };
}