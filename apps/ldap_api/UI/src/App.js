import React, { Component } from 'react';
import { Route, Switch, Redirect } from "react-router";
import './App.css';
import Home from './views/Home';
import Workers from './views/Workers';
import AddExtern from './views/AddExtern';
import Externs from './views/Externs';
import Students from './views/Students';
import Administrators from './views/Administrators';
import Login from './views/Login';
import People from './views/People';
import RecoverPassword from './views/RecoverPassword';
import ChangePassword from './views/ChangePassword';
import SecurityQuestions from './views/SecurityQuestions';
import AddWorker from './views/AddWorker';
import AddStudent from './views/AddStudent';
import MainDrawer from './components/MainDrawer';
import config from './config';
import { ConnectedRouter } from 'connected-react-router'
import { history } from './store/storeConfig'
import {connect} from 'react-redux'
import {userActions} from './actions/authActions'

class App extends Component{
  state = {
    authed: false,
    loading: true
  }

  constructor(props){
    super(props)
  }

  componentWillMount() {
    fetch(config.api_address + '/trabajadores', {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_workers = data.workers;
        if(ldap_workers){
          this.setState({ authed: true });
        }
        this.setState({ loading: false });
      }).catch(err => {
        console.log(err);
        this.setState({ loading: false });
      })
  }

  render(){
    return (
      <ConnectedRouter history={history}>
        <div className="App">
        {this.state.loading ? '' : !this.props.authed ?
          <Switch>
            <Route path='/entrar' render={(routerProps) => (
              <Login {...routerProps}/>
            )} />
            <Route exact path="/p/cambiar" component={ChangePassword} />
            <Route exact path="/p/recuperar" component={RecoverPassword} />
            <Route exact path="/p/preguntasdeseguridad" component={SecurityQuestions} />
            <Route exact path="/p/agregartrabajador" component={AddWorker} />
            <Route exact path="/p/agregarestudiante" component={AddStudent} />
            <Redirect to={{pathname: '/entrar'}} /> 
          </Switch> :
          <MainDrawer authed={this.props.authed}>
            <Switch>
              <Route exact path="/" component={Home} />
              <Route path="/estudiantes" component={Students} />
              <Route path="/trabajadores" component={Workers} />
              <Route path="/externos/agregar" component={AddExtern} />
              <Route exact path="/externos" component={Externs} />
              <Route exact path="/personas" component={People} />
              <Route exact path="/administradores" component={Administrators} />
              <Route exact path="/p/agregartrabajador" component={AddWorker} />
              <Route exact path="/p/agregarestudiante" component={AddStudent} />
              {/* <Route component={Error404} /> */}
            </Switch>
          </MainDrawer>
        }
        </div>
      </ConnectedRouter >
    );
  }
}

const mapStateToProps = (state) => ({
  authed: state.login.loggedIn
});

export default connect(mapStateToProps, {login: userActions.login})(App);
