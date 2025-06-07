import express from 'express';

const app = express();
const PORT = 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.send('Banco A API corriendo');
});

app.listen(PORT, () => {
  console.log(`Servidor de Banco A escuchando en puerto ${PORT}`);
});
