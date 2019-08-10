import * as types from './main';

export const alertActions = {
    success,
    error,
    clear
};

function success(message) {
    return { type: types.ALERTS.SUCCESS, message };
}

function error(message) {
    return { type: types.ALERTS.ERROR, message };
}

function clear() {
    return { type: types.ALERTS.CLEAR };
}