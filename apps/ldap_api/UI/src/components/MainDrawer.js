import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import { withStyles } from '@material-ui/core/styles';
import Drawer from '@material-ui/core/Drawer';
import CssBaseline from '@material-ui/core/CssBaseline';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Button from '@material-ui/core/Button';
import List from '@material-ui/core/List';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import HomeIcon from '@material-ui/icons/Home';
import AdbIcon from '@material-ui/icons/Adb';
import HowToReg from '@material-ui/icons/HowToReg';
import Accessibility from '@material-ui/icons/Accessibility';
import WcIcon from '@material-ui/icons/Wc';
import TransferWithinAStation from '@material-ui/icons/TransferWithinAStation';
import {Switch, Route, Link} from 'react-router-dom';
import {connect} from 'react-redux'
import {userActions} from '../actions/authActions'

const drawerWidth = 240;

const styles = theme => ({
  drawerLink: {
    textDecoration: 'none',
  },
  root: {
    display: 'flex',
  },
  appBar: {
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  appBarShift: {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: drawerWidth,
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  menuButton: {
    marginLeft: 12,
    marginRight: 20,
  },
  hide: {
    display: 'none',
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
  },
  drawerPaper: {
    width: drawerWidth,
  },
  drawerHeader: {
    display: 'flex',
    alignItems: 'center',
    padding: '0 8px',
    ...theme.mixins.toolbar,
    justifyContent: 'flex-end',
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing.unit * 3,
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginLeft: -drawerWidth,
  },
  contentShift: {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  },
});

class MainDrawer extends React.Component {

  constructor(props){
      super(props);
      this.state = {
        open: props.authed,
        admin: localStorage.getItem('currentUserRole') == 'admin'
      };
  }

  handleDrawerOpen = () => {
    this.setState({ open: true });
  };

  handleDrawerClose = () => {
    this.setState({ open: false });
  };

  logout = (event) => {
    event.preventDefault();
    this.props.logout()
  }

  render() {
    const { classes, theme } = this.props;
    const { open } = this.state;

    return (
      <div className={classes.root}>
        <CssBaseline />
        <AppBar
          position="fixed"
          className={classNames(classes.appBar, {
            [classes.appBarShift]: open,
          })}
        >
          <Toolbar disableGutters={!open}>
            <IconButton
              color="inherit"
              aria-label="Open drawer"
              onClick={this.handleDrawerOpen}
              className={classNames(classes.menuButton, open && classes.hide)}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" color="inherit" noWrap>
              Directorio Único de la UH
            </Typography>
            {!this.props.authed ?
            <Button style={{position: 'absolute', right: 20}} color="inherit">
              <Link style={{color: 'white'}} to="/entrar">Entrar</Link>
            </Button> :
            <Button style={{position: 'absolute', right: 20}} color="inherit" onClick={(event) => this.logout(event)}>
              Salir
            </Button>
            }
          </Toolbar>
        </AppBar>
        <Drawer
          className={classes.drawer}
          variant="persistent"
          anchor="left"
          open={open}
          classes={{
            paper: classes.drawerPaper,
          }}
        >
          <div className={classes.drawerHeader}>
            <IconButton onClick={this.handleDrawerClose}>
              {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
          </div>
          <Divider />
          <List>
          { this.state.admin ?  
            [['Inicio', <HomeIcon/>, '/'], ['Personas', <Accessibility/>, '/personas'], 
            ['Estudiantes', <HowToReg/>, '/estudiantes'], ['Trabajadores', <WcIcon/>, '/trabajadores'], 
            ['Externos', <TransferWithinAStation/>, '/externos'], ['Administradores', <AdbIcon/>, '/administradores']].map((obj, index) => (
              <Link to={obj[2]} className={classNames(classes.drawerLink)}>
                <Switch>
                  <Route exact={obj[2] === '/'} path={obj[2]} render={() =>
                    <ListItem selected button key={obj[2]}>
                      <ListItemIcon>{obj[1]}</ListItemIcon>
                      <ListItemText primary={obj[0]} />
                    </ListItem>
                  }/>
                  <Route render={() =>
                    <ListItem button key={obj[0]}>
                      <ListItemIcon>{obj[1]}</ListItemIcon>
                      <ListItemText primary={obj[0]} />
                    </ListItem>
                  }/>
                </Switch>
              </Link>
            )) : [['Inicio', <HomeIcon/>, '/'], ['Personas', <Accessibility/>, '/personas'], 
            ['Estudiantes', <HowToReg/>, '/estudiantes'], ['Trabajadores', <WcIcon/>, '/trabajadores'], 
            ['Externos', <TransferWithinAStation/>, '/externos']].map((obj, index) => (
              <Link to={obj[2]} className={classNames(classes.drawerLink)}>
                <Switch>
                  <Route exact={obj[2] === '/'} path={obj[2]} render={() =>
                    <ListItem selected button key={obj[2]}>
                      <ListItemIcon>{obj[1]}</ListItemIcon>
                      <ListItemText primary={obj[0]} />
                    </ListItem>
                  }/>
                  <Route render={() =>
                    <ListItem button key={obj[0]}>
                      <ListItemIcon>{obj[1]}</ListItemIcon>
                      <ListItemText primary={obj[0]} />
                    </ListItem>
                  }/>
                </Switch>
              </Link>))
            }
          </List>
        </Drawer>
        <main
          className={classNames(classes.content, {
            [classes.contentShift]: open,
          })}
        >
          <div className={classes.drawerHeader} />
            {this.props.children}
        </main>
      </div>
    );
  }
}

MainDrawer.propTypes = {
  classes: PropTypes.object.isRequired,
  theme: PropTypes.object.isRequired,
};

export default connect(() => {}, {logout: userActions.logout})(withStyles(styles, { withTheme: true })(MainDrawer));