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
            res.json().then(data => {
                console.log(res)
                dispatch(push('/p/cambiar?correo='+data.email));
                alert('Trabajador agregado satisfactoriamente con el correo: "'+data.email+'", por favor cambie su contraseña (12345678).');
                dispatch({ 
                    type: types.END_LOADING
                });
            });
            
        } else if(res.status === 403){
            res.json().then(data => {
                console.log(res)
                dispatch(push('/p/cambiar'));
                alert('Este trabajador ya existe en el directorio con el correo: "'+data.email+'".');
                dispatch({ 
                    type: types.END_LOADING
                });
            });
        }else if(res.status === 404){
            alert('Este trabajador no existe en el directorio.');
            dispatch({ 
                type: types.END_LOADING
            });
        }
        
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
                res.json().then(data => {
                    console.log(res)
                    dispatch(push('/p/cambiar?correo='+data.email));
                    alert('Estudiante agregado satisfactoriamente con el correo: "'+data.email+'", por favor cambie su contraseña (12345678).');
                    dispatch({ 
                        type: types.END_LOADING
                    });
                });
                
            } else if(res.status === 403){
                res.json().then(data => {
                    console.log(res)
                    dispatch(push('/p/cambiar'));
                    alert('Este estudiante ya existe en el directorio con el correo: "'+data.email+'".');
                    dispatch({ 
                        type: types.END_LOADING
                    });
                });
            }else if(res.status === 404){
                alert('Este estudiante no existe en el directorio.');
                dispatch({ 
                    type: types.END_LOADING
                });
            }
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