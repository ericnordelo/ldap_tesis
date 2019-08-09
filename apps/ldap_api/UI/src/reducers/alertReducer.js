import { ALERTS } from '../actions/main';

export function alert(state = {}, action) {
    switch (action.type) {
    case ALERTS.SUCCESS:
        return {
        type: 'alert-success',
        message: action.message
        };
    case ALERTS.ERROR:
        return {
        type: 'alert-danger',
        message: action.message
        };
    case ALERTS.CLEAR:
        return {};
    default:
        return state
    }
}