import React from 'react';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';

export default class AddAdminDialog extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      open: false,
      email: props.email,
    }
  }

  handleChange = name => event => {
    this.setState({ [name]: event.target.value });
  };

  handleClickOpen = () => {
    this.setState({ open: true });
  }

  handleClose = () => {
    this.setState({ open: false });
  }

  handleAddAction = () => {
    this.props.addMethod(this.state.email);
  }

  render() {
    return (
      <div style={{marginTop: 30}}>
        <Button variant="contained" size="small" color="primary" onClick={this.handleClickOpen}>
          Agregar Administrador
        </Button>
        <Dialog
          fullWidth
          open={this.state.open}
          onClose={this.handleClose}
          aria-labelledby="form-dialog-title"
        >
          <DialogTitle id="form-dialog-title">Correo del nuevo administrador</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              id="email"
              label="Correo"
              type="email"
              value={this.state.email}
              onChange={this.handleChange("email")}
              fullWidth
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={this.handleClose} color="secondary">
              Cancelar
            </Button>
            <Button onClick={this.handleAddAction} color="primary">
              Agregar
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    )
  }
}