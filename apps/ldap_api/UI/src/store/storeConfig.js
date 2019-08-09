import { createStore, applyMiddleware, compose } from "redux";
import rootReducer from "../reducers/main";
import thunk from "redux-thunk";
import { createBrowserHistory } from 'history'
import { routerMiddleware } from 'connected-react-router'
export const history = createBrowserHistory()

const storeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

function configureStore() {
  const store = createStore(
    rootReducer(history), // root reducer with router state
    compose(
      applyMiddleware(
        routerMiddleware(history), // for dispatching history actions
        thunk
      ),
    ),
  );

  return store;
}
export default configureStore();