import * as types from '../actions/main';

const initialState = [];

export default function(state = initialState, action) {
  switch(action.type) {
    case types.START_LOADING:
      return Object.assign({}, state, {
        loading: true
      });
    case types.END_LOADING:
      return {
        loading: false,
      };
    default:
      return state;
  }
}