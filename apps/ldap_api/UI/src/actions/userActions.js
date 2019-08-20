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
            alert('Trabajador agregado satisfactoriamente con el correo: por favor cambie su contraseña.');
        } else if(res.status === 403){
            alert('Este trabajador ya existe en el directorio con el correo.');
        }else if(res.status === 404){
            alert('Este trabajador no existe en el directorio.');
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
                alert('Estudiante agregado satisfactoriamente con el correo: por favor cambie su contraseña.');
            } else if(res.status === 403){
                alert('Este estudiante ya existe en el directorio.');
            }else if(res.status === 404){
                alert('Este estudiante no existe en el directorio.');
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