import { combineReducers } from 'redux';
import login from './loginReducer';
import general from './generalReducer';
import { connectRouter } from 'connected-react-router'

export default (history) => combineReducers({
  router: connectRouter(history),
  login,
  general
})