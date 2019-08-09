import * as types from '../actions/main';

const initialState = [];

export default function(state = initialState, action) {
  let response = action.response;

  switch(action.type) {
    case types.LOGIN_USER:
      return Object.assign({}, state, {
        loggingIn: true,
        loggedIn: false,
        user: action.user
      });
    case types.LOGIN_USER_SUCCESS:
      return {
        loggingIn: false,
        loggedIn: true,
        user: action.user
      };
    case types.LOGIN_USER_ERROR:
      return {
        loggingIn: false,
        loggedIn: false,
      };
    case types.LOGOUT_USER:
      return {
        loggingIn: false,
        loggedIn: false,
      };
    default:
      return state;
  }
}