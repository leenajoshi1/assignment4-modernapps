import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import PhotoPortal from './PhotoPortal';
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({useNavigate: () => mockNavigate}));
const photo = {id:1,name:'campus.png',date_taken:'2026-11-10',tags:'campus'};
beforeEach(() => {
  jest.clearAllMocks();
  window.jQuery = jest.fn(() => ({modal:jest.fn()}));
});
test('admin sees starter upload form and thumbnail retrieves saved comments', async () => {
  global.fetch = jest.fn(async path => ({ok:true,json:async () => {
    if (path === '/api/session') return {username:'admin',usertype:'admin'};
    if (path === '/api/photos') return {photos:[photo]};
    return {comments:'A sunny afternoon.'};
  }}));
  const {container} = render(<PhotoPortal/>);
  const thumbnail = await screen.findByAltText('campus.png');
  expect(container.querySelector('#uploadPhotoForm')).toBeInTheDocument();
  expect(screen.getByLabelText('Comments')).toBeInTheDocument();
  fireEvent.click(thumbnail);
  expect(await screen.findByText('A sunny afternoon.')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith('/api/photos/campus.png/comments', {credentials:'include'});
  expect(window.jQuery).toHaveBeenCalled();
});
test('general user sees thumbnails without upload form', async () => {
  global.fetch = jest.fn(async path => ({ok:true,json:async () => path === '/api/session' ? {username:'viewer@gmail.com',usertype:'generaluser'} : {photos:[photo]}}));
  const {container} = render(<PhotoPortal/>);
  await screen.findByAltText('campus.png');
  expect(container.querySelector('#uploadPhotoForm')).not.toBeInTheDocument();
});
test('unauthenticated direct portal access returns to login', async () => {
  global.fetch = jest.fn(async () => ({ok:false}));
  render(<PhotoPortal/>);
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/', {replace:true}));
});
