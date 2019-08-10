import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import Toolbar from '@material-ui/core/Toolbar';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import {Link} from 'react-router-dom';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import {sections} from './_sections'
import {footer} from './_footer'

const styles = theme => ({
  layout: {
    width: 'auto',
    marginLeft: theme.spacing.unit * 3,
    marginRight: theme.spacing.unit * 3,
    [theme.breakpoints.up(1100 + theme.spacing.unit * 3 * 2)]: {
      width: 1100,
      marginLeft: 'auto',
      marginRight: 'auto',
    },
  },
  captionLink:{
    color: "black",
  },
  toolbarMain: {
    borderBottom: `1px solid ${theme.palette.grey[300]}`,
  },
  toolbarTitle: {
    flex: 1,
  },
  toolbarSecondary: {
    justifyContent: 'space-between',
  },
  mainFeaturedPost: {
    backgroundColor: theme.palette.grey[800],
    color: theme.palette.common.white,
    marginBottom: theme.spacing.unit * 4,
  },
  mainFeaturedPostContent: {
    padding: `${theme.spacing.unit * 6}px`,
    [theme.breakpoints.up('md')]: {
      paddingRight: 0,
    },
  },
  mainGrid: {
    marginTop: theme.spacing.unit * 3,
  },
  card: {
    display: 'flex',
  },
  cardDetails: {
    flex: 1,
  },
  cardMedia: {
    width: 160,
  },
  markdown: {
    padding: `${theme.spacing.unit * 3}px 0`,
  },
  sidebarAboutBox: {
    padding: theme.spacing.unit * 2,
    backgroundColor: theme.palette.grey[200],
  },
  sidebarSection: {
    marginTop: theme.spacing.unit * 3,
  },
  footer: {
    backgroundColor: theme.palette.background.paper,
    marginTop: theme.spacing.unit * 8,
    padding: `${theme.spacing.unit * 6}px 0`,
  },
  submit: {
    marginTop: 15
  }
});

class AddStudent extends Component{

  constructor(props){
    super(props);
    this.state = {
      ci: '',
      loading: false
    };
  }

  render(){
    const {classes} = this.props;

    return (
      <React.Fragment>
        <CssBaseline />
        <div className={classes.layout}>
          <Toolbar className={classes.toolbarMain}>
            <Typography
              component="h2"
              variant="h5"
              color="inherit"
              align="center"
              noWrap
              className={classes.toolbarTitle}
            >
              Directorio Único UH
            </Typography>

          </Toolbar>
          <Toolbar variant="dense" className={classes.toolbarSecondary}>
            {sections.map(section => (
              <Link to={section[1]}className={classes.captionLink}>
                <Typography color="inherit" noWrap key={section[0]}>
                  {section[0]}
                </Typography>
              </Link>
            ))}
          </Toolbar>
          <main>
            {/* Main featured post */}
            <Paper className={classes.mainFeaturedPost}>
              <Grid container>
                <Grid item md={6}>
                  <div className={classes.mainFeaturedPostContent}>
                    <Typography component="h1" variant="h5" color="inherit" gutterBottom>
                      Agregar Estudiante
                    </Typography>
                  </div>
                </Grid>
              </Grid>
            </Paper>
            <Typography className={classes.subheader} component="h1" variant="h6">
              Chequear CI:
            </Typography>
            <TextField
              id="ci"
              label="Carnet de identidad"
              fullWidth
              margin="normal"
              variant="filled"
              InputLabelProps={{
                shrink: true,
              }}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={this.state.loading}
              className={classes.submit}
            >
              Agregar Estudiante
            </Button>
          </main>
        </div>
        {/* Footer */}
        {footer(classes)}
        {/* End footer */}
      </React.Fragment>
    );
  }
}

AddStudent.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(AddStudent);